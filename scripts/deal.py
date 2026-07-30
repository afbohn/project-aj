#!/usr/bin/env python3
"""
Daily deal operations for Project AJ.

Running a deal touches four things that have to stay in sync: the product's
price, its compare-at price, an inventory snapshot, and the daily_deal
metaobject entry. Doing that by hand every morning is where money leaks, so
this wraps the whole cycle in three commands:

    deal.py plan  <handle> --discount 40      what it would do, changes nothing
    deal.py start <handle> --discount 40      apply the deal
    deal.py end   <handle>                    restore regular pricing
    deal.py status                            what is live right now

Two guarantees it enforces, because neither can be enforced in the theme:

  NEVER BELOW COST. Storefront Liquid cannot read unit cost, so the floor has
  to be applied here. A discount that would price a variant under what we pay
  is clamped to cost, and a product with no cost data is refused outright
  rather than guessed at.

  PRICE ALWAYS RESTORABLE. The regular price is parked in compare_at_price for
  the duration of the deal, which is also what renders the strikethrough. So
  `end` just moves it back. No separate bookkeeping to lose.

THE ONE THING THIS CANNOT DO FOR YOU: `end` has to actually run. The theme
stops SHOWING a deal at ends_at, but the discounted price stays on the product
until something restores it. A deal that ends without `end` running keeps
selling at cost. Schedule it.

Auth comes from the Shopify CLI, so there are no tokens in this file:

    shopify store auth --store <store> --scopes write_products,write_metaobjects,read_inventory
"""

import argparse
import json
import os
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


CENTS = Decimal("0.01")


# --------------------------------------------------------------------------
# Shopify CLI plumbing
# --------------------------------------------------------------------------

from shopify_auth import gql  # noqa: E402  (see module docstring for auth order)


def fetch_product(handle):
    data = gql("""
    {
      productByIdentifier(identifier: {handle: "%s"}) {
        id
        title
        totalInventory
        variants(first: 100) {
          nodes {
            id
            title
            price
            compareAtPrice
            inventoryQuantity
            inventoryItem { tracked unitCost { amount } }
          }
        }
      }
    }
    """ % handle)

    product = (data or {}).get("productByIdentifier")
    if not product:
        sys.exit(f"No product found with handle '{handle}'.")
    return product


# --------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------

def price_variant(variant, discount_pct):
    """Work out the deal price for one variant.

    Returns (regular, cost, deal_price, clamped) with everything as Decimal.
    `clamped` is True when the requested discount would have gone below cost
    and we held the line at cost instead.
    """
    regular = Decimal(variant["price"])
    unit_cost = (variant.get("inventoryItem") or {}).get("unitCost")
    cost = Decimal(unit_cost["amount"]) if unit_cost else None

    if cost is None:
        return regular, None, None, False

    target = (regular * (Decimal(100) - Decimal(discount_pct)) / Decimal(100))
    target = target.quantize(CENTS, rounding=ROUND_HALF_UP)

    # Round the floor UP so a half-cent never lands us a fraction under cost.
    floor = cost.quantize(CENTS, rounding=ROUND_CEILING)

    if target < floor:
        return regular, cost, floor, True
    return regular, cost, target, False


def analyse(product, discount_pct):
    rows = []
    for v in product["variants"]["nodes"]:
        regular, cost, deal, clamped = price_variant(v, discount_pct)
        rows.append({
            "id": v["id"],
            "title": v["title"],
            "regular": regular,
            "cost": cost,
            "deal": deal,
            "clamped": clamped,
            # The supplier's own MSRP, when Collective synced one. Preserved
            # rather than overwritten — see apply_deal().
            "existing_compare_at": v["compareAtPrice"],
            "on_deal_already": v["compareAtPrice"] is not None,
        })
    return rows


def report(product, rows, discount_pct, live_deal=False):
    print(f"\n{product['title']}")
    print(f"requested discount: {discount_pct}%\n")
    print(f"{'VARIANT':30} {'REGULAR':>9} {'COST':>8} {'DEAL':>9} {'MARGIN':>9} {'OFF':>6}")
    print("-" * 76)

    for r in rows:
        if r["cost"] is None:
            print(f"{r['title'][:29]:30} {r['regular']:>9} {'—':>8} {'—':>9} {'NO COST':>9} {'—':>6}")
            continue
        margin = r["deal"] - r["cost"]
        off = (r["regular"] - r["deal"]) / r["regular"] * 100
        flag = "  <- held at cost" if r["clamped"] else ""
        print(f"{r['title'][:29]:30} {r['regular']:>9} {r['cost']:>8} {r['deal']:>9} "
              f"{margin:>9} {off:>5.0f}%{flag}")

    missing = [r for r in rows if r["cost"] is None]
    clamped = [r for r in rows if r["clamped"]]
    msrp = [r for r in rows if r["existing_compare_at"]]

    print()
    if missing:
        print(f"REFUSING: {len(missing)} variant(s) have no cost data. Cannot guarantee "
              f"we stay above cost, so nothing will be changed.")
    if clamped:
        print(f"NOTE: {len(clamped)} variant(s) would have priced below cost at "
              f"{discount_pct}%. Held at cost — margin is zero, not negative.")
    if msrp:
        print(f"NOTE: {len(msrp)} variant(s) already carry a supplier compare-at "
              f"price (MSRP). It will be kept, and the discount will show against "
              f"it rather than against our price.")
    if live_deal:
        print("REFUSING: a deal is already running on this product. Run `end` first.")

    return not missing and not live_deal


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_plan(args):
    product = fetch_product(args.handle)
    rows = analyse(product, args.discount)
    ok = report(product, rows, args.discount)
    print("\nThis was a dry run. Nothing changed." if ok else "")


def cmd_start(args):
    product = fetch_product(args.handle)
    rows = analyse(product, args.discount)
    if not report(product, rows, args.discount, product_has_live_deal(product["id"])):
        sys.exit(1)

    snapshot_map = apply_deal(product, rows)
    print(f"Repriced {len(rows)} variant(s).")

    # Snapshot inventory BEFORE the deal opens. The claimed bar measures the
    # drop from this number, so it has to be taken now, not later.
    snapshot = sum(
        v["inventoryQuantity"]
        for v in product["variants"]["nodes"]
        if (v.get("inventoryItem") or {}).get("tracked") and v["inventoryQuantity"] > 0
    )

    starts = datetime.now(timezone.utc)
    ends = starts + timedelta(hours=args.hours)
    fmt = "%Y-%m-%dT%H:%M:%SZ"

    # Record exactly what each variant cost before the deal. Ending the deal
    # replays this, rather than inferring the old price from compare_at_price.
    # That inference breaks the moment compare-at is populated by anything
    # other than us — enabling Collective's MSRP sync would do it — and an
    # unattended sweep acting on that would raise prices on products that were
    # never on deal.
    price_snapshot = json.dumps(snapshot_map)

    # The lowest price the deal actually ran at. Kept so the past-deals list
    # can show what was on offer after the product has gone back to full price
    # — by then nothing on the product itself remembers.
    deal_price = min(r["deal"] for r in rows)

    fields = [
        ("product", product["id"]),
        ("starts_at", starts.strftime(fmt)),
        ("ends_at", ends.strftime(fmt)),
        ("units_allocated", str(args.units)),
        ("starting_inventory", str(snapshot)),
        ("price_snapshot", price_snapshot),
        ("deal_price", str(deal_price)),
    ]
    if args.headline:
        fields.append(("headline", args.headline))

    field_gql = ", ".join(
        '{ key: "%s", value: %s }' % (k, json.dumps(v)) for k, v in fields
    )
    result = gql("""
    mutation {
      metaobjectCreate(metaobject: { type: "daily_deal", fields: [%s] }) {
        metaobject { handle }
        userErrors { field message }
      }
    }
    """ % field_gql, mutation=True)

    errors = result["metaobjectCreate"]["userErrors"]
    if errors:
        sys.exit(f"Deal created prices but metaobject failed: {errors}\n"
                 f"Run `end {args.handle}` to restore pricing.")

    handle = result["metaobjectCreate"]["metaobject"]["handle"]
    print(f"Deal {handle} live until {ends.strftime(fmt)} "
          f"({args.hours}h), {snapshot} units in stock, {args.units} allocated.")
    print(f"\nREMEMBER: run `deal.py end {args.handle}` when it finishes, or the "
          f"discounted price stays on the product.")


def apply_deal(product, rows):
    """Reprice for a deal and return the snapshot needed to undo it.

    PRESERVES AN EXISTING COMPARE-AT. Several suppliers sync a real MSRP
    through Collective — the Panama Hats carry $293.00 against a $249.05 price.
    Overwriting that with the current price would destroy genuine data, and
    clearing it on `end` would delete it permanently. It is also the better
    anchor: discounting against a true MSRP shows a larger and still-honest
    saving than discounting against our own price.

    So compare-at is only written where there was none, and the snapshot records
    what each field held so `end` restores both exactly.
    """
    updates = []
    snapshot = {}
    for r in rows:
        if r["existing_compare_at"]:
            # Leave compare-at alone; only the price moves.
            updates.append('{ id: "%s", price: "%s" }' % (r["id"], r["deal"]))
        else:
            updates.append('{ id: "%s", price: "%s", compareAtPrice: "%s" }'
                           % (r["id"], r["deal"], r["regular"]))
        snapshot[str(r["id"])] = {
            "price": str(r["regular"]),
            "compare_at": str(r["existing_compare_at"]) if r["existing_compare_at"] else None,
        }

    result = gql("""
    mutation {
      productVariantsBulkUpdate(productId: "%s", variants: [%s]) {
        userErrors { field message }
      }
    }
    """ % (product["id"], ",\n".join(updates)), mutation=True)
    errs = result["productVariantsBulkUpdate"]["userErrors"]
    if errs:
        sys.exit(f"Repricing failed: {errs}")
    return snapshot


def product_has_live_deal(product_gid):
    """True when an activated deal is running on this product right now.

    Presence of a compare-at price is NOT the test — suppliers set those. Only
    an entry with a price_snapshot represents a deal we applied.
    """
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 100) {
        nodes { fields { key value } }
      }
    }
    """)
    now = datetime.now(timezone.utc)
    for node in data["metaobjects"]["nodes"]:
        f = {x["key"]: x["value"] for x in node["fields"]}
        if f.get("product") != product_gid or not f.get("price_snapshot"):
            continue
        try:
            starts = datetime.fromisoformat(f["starts_at"].replace("Z", "+00:00"))
            ends = datetime.fromisoformat(f["ends_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if starts <= now < ends:
            return True
    return False


def entries_for_product(product_gid):
    """Every daily_deal entry pointing at this product, newest window last."""
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 100) {
        nodes { id handle fields { key value } }
      }
    }
    """)
    out = []
    for node in data["metaobjects"]["nodes"]:
        f = {x["key"]: x["value"] for x in node["fields"]}
        if f.get("product") == product_gid:
            out.append({"id": node["id"], "handle": node["handle"], "fields": f})
    return out


def _snapshot_entry(raw):
    """Normalise a snapshot entry to (price, compare_at).

    Two formats exist. Early deals stored just the price as a string; current
    ones store {"price", "compare_at"} so a supplier MSRP can be put back
    exactly as it was. Old entries are read as "no compare-at recorded", which
    matches how they were written.
    """
    if isinstance(raw, dict):
        return raw.get("price"), raw.get("compare_at")
    return raw, None


def restore_prices(product, snapshot):
    """Put variant prices back, and compare-at back to whatever it was.

    Variants missing from the snapshot are left alone: one added mid-deal was
    never repriced by us, so we have no business writing to it.
    """
    targets = []
    for v in product["variants"]["nodes"]:
        if v["id"] not in snapshot:
            continue
        price, compare_at = _snapshot_entry(snapshot[v["id"]])
        if v["price"] != price or v["compareAtPrice"] != compare_at:
            targets.append((v, price, compare_at))
    if not targets:
        return 0

    updates = ",\n".join(
        '{ id: "%s", price: "%s", compareAtPrice: %s }'
        % (v["id"], price, f'"{compare_at}"' if compare_at else "null")
        for v, price, compare_at in targets
    )
    result = gql("""
    mutation {
      productVariantsBulkUpdate(productId: "%s", variants: [%s]) {
        userErrors { field message }
      }
    }
    """ % (product["id"], updates), mutation=True)

    errors = result["productVariantsBulkUpdate"]["userErrors"]
    if errors:
        sys.exit(f"Restore failed: {errors}")
    return len(targets)


def cmd_end(args):
    product = fetch_product(args.handle)

    # Prefer the snapshot recorded at start. Fall back to compare_at_price only
    # for deals started before snapshots existed.
    snapshot = {}
    for entry in entries_for_product(product["id"]):
        raw = entry["fields"].get("price_snapshot")
        if raw:
            try:
                snapshot = json.loads(raw)
            except json.JSONDecodeError:
                pass

    if snapshot:
        n = restore_prices(product, snapshot)
        print(f"{product['title']}: restored {n} variant(s) from the price snapshot."
              if n else f"{product['title']}: prices already match the snapshot.")
        closed = close_active_entries(product["id"])
        print(f"Closed {closed} active deal entr{'y' if closed == 1 else 'ies'}."
              if closed else "No active deal entry was pointing at this product.")
        return

    rows = [v for v in product["variants"]["nodes"] if v["compareAtPrice"] is not None]

    if not rows:
        # Pricing is already back to normal, but a live entry can still be
        # pointing at this product — that is exactly the half-ended state this
        # command exists to clean up, so carry on to the metaobject below
        # rather than returning here.
        print(f"{product['title']}: no compare-at prices set — pricing already normal.")
        closed = close_active_entries(product["id"])
        print(f"Closed {closed} active deal entr{'y' if closed == 1 else 'ies'}."
              if closed else "No active deal entry was pointing at this product.")
        return

    # compare_at holds the regular price. Move it back and clear the strike.
    updates = ",\n".join(
        '{ id: "%s", price: "%s", compareAtPrice: null }' % (v["id"], v["compareAtPrice"])
        for v in rows
    )
    result = gql("""
    mutation {
      productVariantsBulkUpdate(productId: "%s", variants: [%s]) {
        productVariants { id price compareAtPrice }
        userErrors { field message }
      }
    }
    """ % (product["id"], updates), mutation=True)

    errors = result["productVariantsBulkUpdate"]["userErrors"]
    if errors:
        sys.exit(f"Restore failed: {errors}")
    print(f"{product['title']}: restored regular pricing on {len(rows)} variant(s).")

    # Close the metaobject too. Restoring the price without this leaves the
    # section advertising a deal on a product that is back at full price —
    # worse than either state on its own. We wind ends_at back to now rather
    # than deleting, so the deal stays in the history.
    closed = close_active_entries(product["id"])
    if closed:
        print(f"Closed {closed} active deal entr{'y' if closed == 1 else 'ies'}.")
    else:
        print("No active deal entry was pointing at this product.")


def close_active_entries(product_gid):
    """Wind ends_at back to now for any live entry referencing this product."""
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 50) {
        nodes { id fields { key value } }
      }
    }
    """)

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    closed = 0

    for node in data["metaobjects"]["nodes"]:
        f = {x["key"]: x["value"] for x in node["fields"]}
        if f.get("product") != product_gid:
            continue
        try:
            ends = datetime.fromisoformat(f["ends_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if ends <= now:
            continue  # already over

        result = gql("""
        mutation {
          metaobjectUpdate(
            id: "%s",
            metaobject: { fields: [{ key: "ends_at", value: "%s" }] }
          ) { userErrors { message } }
        }
        """ % (node["id"], stamp), mutation=True)

        errs = result["metaobjectUpdate"]["userErrors"]
        if errs:
            print(f"  warning: could not close {node['id']}: {errs}")
        else:
            closed += 1

    return closed


def cmd_queue(args):
    """Schedule a deal to begin later, without touching prices now.

    `start` reprices immediately, which is wrong for anything scheduled: it
    would discount the product while a different deal is still running, and it
    would snapshot inventory hours before the deal opens — making the claimed
    bar measure sales that happened outside the deal.

    So this records intent only. `activate` does the repricing when the window
    actually opens. An entry with a start time in the past and no
    price_snapshot is precisely "queued but not yet activated".
    """
    product = fetch_product(args.handle)
    rows = analyse(product, args.discount)

    # Validate the economics now rather than discovering them at activation,
    # when nobody is watching. The compare-at check from `start` is deliberately
    # skipped: another deal may legitimately be running today.
    # live_deal=False on purpose: this deal starts later, so whether one is
    # running right now says nothing about whether it can be queued. activate
    # re-checks at the moment it matters.
    report(product, rows, args.discount, live_deal=False)
    if any(r["cost"] is None for r in rows):
        sys.exit(1)

    try:
        starts = datetime.fromisoformat(args.starts_at.replace("Z", "+00:00"))
    except ValueError:
        sys.exit(f"Could not parse --starts-at {args.starts_at!r}. "
                 "Use an ISO timestamp like 2026-07-30T19:36:00Z.")
    if starts.tzinfo is None:
        starts = starts.replace(tzinfo=timezone.utc)
    ends = starts + timedelta(hours=args.hours)
    fmt = "%Y-%m-%dT%H:%M:%SZ"

    fields = [
        ("product", product["id"]),
        ("starts_at", starts.strftime(fmt)),
        ("ends_at", ends.strftime(fmt)),
        ("units_allocated", str(args.units)),
        ("discount_percent", str(args.discount)),
    ]
    if args.headline:
        fields.append(("headline", args.headline))

    field_gql = ", ".join('{ key: "%s", value: %s }' % (k, json.dumps(v)) for k, v in fields)
    result = gql("""
    mutation {
      metaobjectCreate(metaobject: { type: "daily_deal", fields: [%s] }) {
        metaobject { handle }
        userErrors { field message }
      }
    }
    """ % field_gql, mutation=True)

    errors = result["metaobjectCreate"]["userErrors"]
    if errors:
        sys.exit(f"Queue failed: {errors}")

    handle = result["metaobjectCreate"]["metaobject"]["handle"]
    print(f"\nQueued {handle}: {args.discount}% off {product['title'][:40]}")
    print(f"  starts {starts.strftime(fmt)}  ends {ends.strftime(fmt)}")
    print("\nPrices are UNCHANGED. `deal.py activate` applies them when the")
    print("window opens — that runs hourly in CI, so nothing to do by hand.")


def cmd_activate(args):
    """Apply any queued deal whose window has opened.

    Safe to run repeatedly: a deal is only activated when it has a
    discount_percent, its window contains now, and it has no price_snapshot yet.
    Writing the snapshot is what marks it activated, so a second run finds
    nothing.
    """
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 100) {
        nodes { id handle fields { key value } }
      }
    }
    """)

    now = datetime.now(timezone.utc)
    activated = 0

    for node in data["metaobjects"]["nodes"]:
        f = {x["key"]: x["value"] for x in node["fields"]}
        if f.get("price_snapshot"):
            continue  # already activated
        if not f.get("discount_percent") or not f.get("product"):
            continue  # not a queued deal
        try:
            starts = datetime.fromisoformat(f["starts_at"].replace("Z", "+00:00"))
            ends = datetime.fromisoformat(f["ends_at"].replace("Z", "+00:00"))
            discount = float(f["discount_percent"])
        except (KeyError, ValueError):
            continue
        if not (starts <= now < ends):
            continue  # not due, or already over — an unactivated expired deal
                      # is simply skipped rather than applied late

        product = gql("""
        {
          product(id: "%s") {
            id
            title
            totalInventory
            variants(first: 100) {
              nodes {
                id title price compareAtPrice inventoryQuantity
                inventoryItem { tracked unitCost { amount } }
              }
            }
          }
        }
        """ % f["product"]).get("product")

        if not product:
            print(f"{node['handle']}: product no longer exists, skipping.")
            continue

        rows = analyse(product, discount)
        if any(r["cost"] is None for r in rows):
            print(f"{node['handle']}: missing cost data, refusing to price.")
            continue
        if product_has_live_deal(product["id"]):
            # A deal we applied is already running here. Repricing on top would
            # compound the discount. Presence of a compare-at price is NOT the
            # test — suppliers set those.
            print(f"{node['handle']}: another deal is already live on "
                  f"{product['title'][:40]}. Skipping.")
            continue

        snapshot_map = apply_deal(product, rows)

        # Snapshot inventory NOW, as the deal opens — that is what the claimed
        # bar measures the drop from.
        snapshot = sum(
            v["inventoryQuantity"]
            for v in product["variants"]["nodes"]
            if (v.get("inventoryItem") or {}).get("tracked") and v["inventoryQuantity"] > 0
        )
        price_snapshot = json.dumps(snapshot_map)
        deal_price = min(r["deal"] for r in rows)

        upd = ", ".join('{ key: "%s", value: %s }' % (k, json.dumps(v)) for k, v in [
            ("price_snapshot", price_snapshot),
            ("starting_inventory", str(snapshot)),
            ("deal_price", str(deal_price)),
        ])
        gql("""
        mutation {
          metaobjectUpdate(id: "%s", metaobject: { fields: [%s] }) {
            userErrors { message }
          }
        }
        """ % (node["id"], upd), mutation=True)

        activated += 1
        print(f"{node['handle']}: activated {discount}% off {product['title'][:40]} "
              f"({len(rows)} variants, {snapshot} in stock)")

    print(f"Activated {activated} deal(s)." if activated
          else "Nothing to activate — no queued deal is due.")


def cmd_sweep(args):
    """End every deal whose window has closed.

    This is the safety net, meant to run unattended on a schedule. The theme
    stops SHOWING a deal the moment ends_at passes, but the discounted price
    stays on the product until something puts it back — so a deal that ends
    while nobody is watching keeps selling at deal price indefinitely. That is
    the single most expensive way this system can fail, and it fails silently.

    Only touches products with a recorded price snapshot, and only writes
    variants whose current price differs from it. Running it repeatedly is
    harmless: the second run finds nothing to do.
    """
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 100) {
        nodes { id handle fields { key value } }
      }
    }
    """)

    now = datetime.now(timezone.utc)
    swept = 0

    def window(fields):
        return (
            datetime.fromisoformat(fields["starts_at"].replace("Z", "+00:00")),
            datetime.fromisoformat(fields["ends_at"].replace("Z", "+00:00")),
        )

    # Products with a deal running RIGHT NOW must not be touched. Without this
    # guard an old expired entry restores its own snapshot over the top of the
    # current deal — Monday's finished deal quietly undoing Friday's live one,
    # on a schedule, with nobody watching. Observed in testing.
    live_products = set()
    latest_expired = {}
    for node in data["metaobjects"]["nodes"]:
        f = {x["key"]: x["value"] for x in node["fields"]}
        if not f.get("product"):
            continue
        try:
            starts, ends = window(f)
        except (KeyError, ValueError):
            continue
        if starts <= now < ends:
            live_products.add(f["product"])
        elif ends <= now:
            # Keyed on starts_at, not ends_at: the deal that most recently
            # STARTED is the one whose repricing is currently in effect, and so
            # the only one whose snapshot describes the prices to restore. An
            # earlier deal can carry a later ends_at once a window is edited,
            # and picking by ends_at then selects a stale entry and sweeps
            # nothing. Observed in testing.
            prev = latest_expired.get(f["product"])
            if prev is None or starts > prev[0]:
                latest_expired[f["product"]] = (starts, node)

    candidates = [node for gid, (_, node) in latest_expired.items()
                  if gid not in live_products]

    skipped = len(latest_expired) - len(candidates)
    if skipped:
        print(f"Skipping {skipped} product(s) with a deal currently running.")

    for node in candidates:
        f = {x["key"]: x["value"] for x in node["fields"]}
        raw = f.get("price_snapshot")
        if not raw:
            continue
        try:
            snapshot = json.loads(raw)
        except json.JSONDecodeError:
            continue

        product = gql("""
        {
          product(id: "%s") {
            id
            title
            variants(first: 100) { nodes { id price compareAtPrice } }
          }
        }
        """ % f["product"]).get("product")

        if not product:
            print(f"{node['handle']}: product no longer exists, skipping.")
            continue

        n = restore_prices(product, snapshot)
        if n:
            swept += 1
            print(f"{node['handle']}: restored {n} variant(s) on {product['title'][:48]}.")

    print(f"Swept {swept} expired deal(s)." if swept
          else "Nothing to sweep — no expired deal is still discounted.")


def cmd_status(args):
    data = gql("""
    {
      metaobjects(type: "daily_deal", first: 50) {
        nodes {
          handle
          fields { key value }
        }
      }
    }
    """)
    now = datetime.now(timezone.utc)
    nodes = data["metaobjects"]["nodes"]
    if not nodes:
        print("No daily_deal entries exist.")
        return

    print(f"{'HANDLE':26} {'STATE':10} {'STARTS':21} {'ENDS':21} {'UNITS':>6}")
    print("-" * 88)
    for n in nodes:
        f = {x["key"]: x["value"] for x in n["fields"]}
        try:
            starts = datetime.fromisoformat(f["starts_at"].replace("Z", "+00:00"))
            ends = datetime.fromisoformat(f["ends_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        state = "LIVE" if starts <= now < ends else ("expired" if ends <= now else "scheduled")
        print(f"{n['handle'][:25]:26} {state:10} {f['starts_at']:21} {f['ends_at']:21} "
              f"{f.get('units_allocated','—'):>6}")

    print("\nAnything marked `expired` whose product still has a compare-at price "
          "is still selling at its deal price. Run `end` on it.")


def main():
    p = argparse.ArgumentParser(description="Project AJ daily deal operations.")
    sub = p.add_subparsers(dest="command", required=True)

    for name, fn, needs_discount in (("plan", cmd_plan, True), ("start", cmd_start, True)):
        sp = sub.add_parser(name)
        sp.add_argument("handle", help="product handle")
        sp.add_argument("--discount", type=float, required=True, help="percent off, e.g. 40")
        sp.add_argument("--hours", type=int, default=24, help="deal duration (start only)")
        sp.add_argument("--units", type=int, default=100, help="units allocated (start only)")
        sp.add_argument("--headline", default="", help="eyebrow text (start only)")
        sp.set_defaults(func=fn)

    sp = sub.add_parser("end")
    sp.add_argument("handle", help="product handle")
    sp.set_defaults(func=cmd_end)

    sp = sub.add_parser("queue", help="schedule a deal for later without changing prices now")
    sp.add_argument("handle", help="product handle")
    sp.add_argument("--discount", type=float, required=True, help="percent off, e.g. 45")
    sp.add_argument("--starts-at", required=True,
                    help="ISO timestamp, e.g. 2026-07-30T19:36:00Z")
    sp.add_argument("--hours", type=int, default=24, help="deal duration")
    sp.add_argument("--units", type=int, default=50, help="units allocated")
    sp.add_argument("--headline", default="Yoink of the Day")
    sp.set_defaults(func=cmd_queue)

    sp = sub.add_parser("activate", help="apply any queued deal whose window has opened")
    sp.set_defaults(func=cmd_activate)

    sp = sub.add_parser("sweep", help="end every deal whose window has closed")
    sp.set_defaults(func=cmd_sweep)

    sp = sub.add_parser("status")
    sp.set_defaults(func=cmd_status)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
