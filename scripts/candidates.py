#!/usr/bin/env python3
"""
Rank the catalogue by how deep a discount it can carry and still make money.

THE QUESTION THIS ANSWERS. A daily deal wants the biggest headline discount it
can honestly show. But "40% off" is only affordable if the margin covers it, and
margin here is set per supplier — 50% from some, 30% from others. So the deepest
discount a product can carry is a property of that product, and it is knowable:
Shopify exposes unit cost on every variant.

    max discount = (price - cost - margin_floor) / price

Computed per variant and then MINIMISED across the product, because deal.py
applies one percentage to every variant. A product whose cheapest variant has
thin margin cannot carry a deep discount even if its expensive variants could —
using the average would quietly sell some variants at a loss.

    python3 scripts/candidates.py                      # keep $2/unit
    python3 scripts/candidates.py --min-margin 5       # keep $5/unit
    python3 scripts/candidates.py --min-margin 0       # break-even is fine
    python3 scripts/candidates.py --min-savings 15     # only big-ticket savings

WHAT MAKES A GOOD DEAL, and why the columns are what they are:

  DISC%   the headline. What the badge will say.
  SAVE$   absolute savings. "$16 off" persuades where "$2 off" does not, even at
          the same percentage — so a high percentage on a $5 item is a weak deal.
  MARGIN  what you keep per unit at that price. Never below --min-margin.
  STOCK   supplier inventory. Thin stock risks selling out early and turning the
          claimed bar into a dead end.

Products with no cost data are excluded rather than guessed at, and products
with no image are flagged: the deal section and the Instagram post both need one.
"""

import argparse
import sys
from decimal import Decimal, ROUND_DOWN

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))

from shopify_auth import gql  # noqa: E402  (see module docstring for auth order)


def fetch_products():
    products, cursor = [], None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = gql("""
        {
          products(first: 100%s, query: "status:active") {
            pageInfo { hasNextPage endCursor }
            nodes {
              title
              handle
              vendor
              totalInventory
              featuredMedia { id }
              variants(first: 100) {
                nodes {
                  price
                  compareAtPrice
                  inventoryQuantity
                  inventoryItem { unitCost { amount } }
                }
              }
            }
          }
        }
        """ % after)
        page = data["products"]
        products.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return products
        cursor = page["pageInfo"]["endCursor"]


def evaluate(product, margin_floor, margin_pct=0.0):
    """Deepest uniform discount this product can carry, or None.

    `margin_floor` is a flat amount per unit; `margin_pct` is a share of the
    deal price. The binding constraint is whichever is larger, which is what
    stops a flat floor from waving through absurd cases: $2 on a $127 hat is
    1.6% margin, and one return then costs more than sixty sales earn.
    """
    variants = product["variants"]["nodes"]
    if not variants:
        return None

    worst_discount = None
    display_price = None
    display_cost = None

    for v in variants:
        uc = (v.get("inventoryItem") or {}).get("unitCost")
        if not uc:
            # One variant without cost data makes the whole product unsafe to
            # discount uniformly — we cannot prove it stays above cost.
            return None
        price = Decimal(v["price"])
        cost = Decimal(uc["amount"])
        if price <= 0:
            return None

        # A percentage floor is defined against the DEAL price, which is not
        # known until the discount is. Solve it directly instead of iterating:
        #   deal >= cost + pct*deal   ->   deal >= cost / (1 - pct)
        floor_from_pct = Decimal(0)
        if margin_pct > 0:
            pct = Decimal(str(margin_pct)) / Decimal(100)
            if pct >= 1:
                return None
            floor_from_pct = (cost / (Decimal(1) - pct)) - cost

        effective_floor = max(margin_floor, floor_from_pct)
        headroom = price - cost - effective_floor
        if headroom <= 0:
            return None  # cannot even hold the floor at full price

        d = (headroom / price)
        if worst_discount is None or d < worst_discount:
            worst_discount = d

        # Report against the variant a shopper sees first: the cheapest.
        if display_price is None or price < display_price:
            display_price, display_cost = price, cost

    pct = (worst_discount * 100).quantize(Decimal("1"), rounding=ROUND_DOWN)
    if pct <= 0:
        return None

    deal_price = (display_price * (Decimal(100) - pct) / Decimal(100)).quantize(Decimal("0.01"))
    return {
        "title": product["title"],
        "handle": product["handle"],
        "vendor": product["vendor"] or "-",
        "price": display_price,
        "cost": display_cost,
        "pct": pct,
        "deal_price": deal_price,
        "savings": display_price - deal_price,
        "margin": deal_price - display_cost,
        "stock": product["totalInventory"] or 0,
        "has_image": bool(product.get("featuredMedia")),
    }


def main():
    ap = argparse.ArgumentParser(description="Find products that can carry a deep discount profitably.")
    ap.add_argument("--min-margin", type=float, default=2.0,
                    help="dollars to keep per unit (default 2). 0 allows break-even.")
    ap.add_argument("--min-margin-pct", type=float, default=0.0,
                    help="also keep at least this %% of the deal price as margin. "
                         "Guards against thin margin on expensive items, where one "
                         "return costs more than many sales earn.")
    ap.add_argument("--max-price", type=float, default=0.0,
                    help="ignore products above this price. Break-even is safe on "
                         "cheap goods and dangerous on dear ones: a return on a $10 "
                         "item costs a little, on a $137 item it costs $137.")
    ap.add_argument("--min-savings", type=float, default=0.0,
                    help="only show deals saving at least this many dollars")
    ap.add_argument("--min-stock", type=int, default=25,
                    help="skip products with less inventory than this (default 25)")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--vendor", default="", help="restrict to one vendor")
    args = ap.parse_args()

    floor = Decimal(str(args.min_margin))
    products = fetch_products()

    rows, no_cost = [], 0
    for p in products:
        if args.vendor and (p["vendor"] or "").lower() != args.vendor.lower():
            continue
        r = evaluate(p, floor, args.min_margin_pct)
        if r is None:
            no_cost += 1
            continue
        if args.max_price and r["price"] > Decimal(str(args.max_price)):
            continue
        if r["savings"] < Decimal(str(args.min_savings)):
            continue
        if r["stock"] < args.min_stock:
            continue
        rows.append(r)

    # Sort by headline percentage, then by absolute savings — a big percentage
    # on a cheap item is a weaker deal than the same percentage on a dear one.
    rows.sort(key=lambda r: (-r["pct"], -r["savings"]))

    limits = [f"${args.min_margin:g}/unit"]
    if args.min_margin_pct:
        limits.append(f"{args.min_margin_pct:g}% of deal price")
    limits.append(f"{args.min_stock}+ stock")
    if args.max_price:
        limits.append(f"price <= ${args.max_price:g}")
    if args.min_savings:
        limits.append(f"savings >= ${args.min_savings:g}")
    print(f"\n{len(products)} active products | {len(rows)} viable at "
          + ", ".join(limits))
    if no_cost:
        print(f"{no_cost} excluded (missing cost data, or cannot hold the margin floor)")
    print()

    if not rows:
        print("Nothing qualifies. Try --min-margin 0 or a lower --min-stock.")
        return

    print(f"{'PRODUCT':32} {'VENDOR':20} {'WAS':>7} {'DEAL':>7} {'SAVE$':>7} "
          f"{'DISC%':>6} {'MARGIN':>7} {'STOCK':>7}")
    print("-" * 104)
    for r in rows[:args.limit]:
        flag = "" if r["has_image"] else "  [no image]"
        # Margin as a share of what the customer pays. Under 5% means a single
        # return outweighs roughly twenty sales.
        if r["deal_price"] > 0 and (r["margin"] / r["deal_price"]) < Decimal("0.05"):
            flag += "  [thin: return risk]"
        print(f"{r['title'][:31]:32} {r['vendor'][:19]:20} {r['price']:>7} "
              f"{r['deal_price']:>7} {r['savings']:>7} {r['pct']:>5}% "
              f"{r['margin']:>7} {r['stock']:>7}{flag}")

    best = rows[0]
    print(f"\nTop pick: {best['title']}")
    print(f"  python3 scripts/deal.py plan {best['handle']} --discount {best['pct']}")


if __name__ == "__main__":
    main()
