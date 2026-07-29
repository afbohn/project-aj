#!/usr/bin/env python3
"""
Keep one automated collection per vendor, handled `vendor-<name>`.

These exist so the theme can answer "what else does this supplier make?".
Liquid can look a collection up by handle but cannot query products by vendor,
so a predictable handle per vendor is the only way to reach that set from the
cart or a product page.

It matters for the cart upsell specifically. Every Shopify Collective supplier
ships its own items, so a cart mixing vendors arrives as separate parcels.
Recommending something from a vendor ALREADY in the cart is therefore the one
suggestion that adds no extra shipment — a real reason for the shopper to say
yes, not just a nudge.

Re-run after importing from a new supplier. Existing collections are left
alone, so it is safe to run repeatedly.

    python3 scripts/vendors.py --dry-run
    python3 scripts/vendors.py
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))

PREFIX = "vendor-"


from shopify_auth import gql  # noqa: E402  (see module docstring for auth order)


def handleize(value):
    """Match Shopify's `handleize` filter, which the theme uses to build the
    same handle from a vendor name at render time. If these two ever disagree
    the lookup silently returns nothing, so keep them in step."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def fetch_vendors():
    vendors, cursor = set(), None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = gql("""
        {
          products(first: 250%s) {
            pageInfo { hasNextPage endCursor }
            nodes { vendor }
          }
        }
        """ % after)
        page = data["products"]
        for n in page["nodes"]:
            if n["vendor"]:
                vendors.add(n["vendor"])
        if not page["pageInfo"]["hasNextPage"]:
            return sorted(vendors)
        cursor = page["pageInfo"]["endCursor"]


def fetch_existing():
    handles, cursor = {}, None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = gql("""
        {
          collections(first: 250%s) {
            pageInfo { hasNextPage endCursor }
            nodes { id handle title }
          }
        }
        """ % after)
        page = data["collections"]
        for n in page["nodes"]:
            handles[n["handle"]] = n["id"]
        if not page["pageInfo"]["hasNextPage"]:
            return handles
        cursor = page["pageInfo"]["endCursor"]


def publication_ids():
    """Sales channels to publish new collections to.

    Returns [] rather than exiting when the credentials cannot read
    publications, which a minimal custom app cannot — that needs
    read_publications. Failing hard here used to abort the whole run BEFORE
    anything was created, so the script reported collections it had not made.
    Unattended, a partial run that says so is far better than a clean-looking
    run that did nothing.
    """
    try:
        data = gql("{ publications(first: 10) { nodes { id name } } }")
    except SystemExit:
        print("  note: cannot read publications (needs read_publications).\n"
              "        Collections will be created but NOT published, so they\n"
              "        will 404 on the storefront until published by hand.")
        return []
    wanted = {"Online Store", "Shop"}
    return [n["id"] for n in data["publications"]["nodes"] if n["name"] in wanted]


def main():
    ap = argparse.ArgumentParser(description="Sync one collection per vendor.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    vendors = fetch_vendors()
    existing = fetch_existing()

    missing = [v for v in vendors if PREFIX + handleize(v) not in existing]

    print(f"{len(vendors)} vendor(s), {len(vendors) - len(missing)} already have a collection\n")
    if not missing:
        print("Nothing to create.")
        return

    for v in missing:
        print(f"  + {PREFIX + handleize(v):34} {v}")

    if args.dry_run:
        print(f"\nDry run — {len(missing)} collection(s) would be created.")
        return

    pubs = publication_ids()
    unpublished = []
    print()

    for v in missing:
        handle = PREFIX + handleize(v)
        # Escaped through json.dumps so vendor names containing quotes or
        # backslashes cannot break out of the GraphQL string.
        result = gql("""
        mutation {
          collectionCreate(input: {
            title: %s,
            handle: %s,
            sortOrder: BEST_SELLING,
            ruleSet: { appliedDisjunctively: false, rules: [
              { column: VENDOR, relation: EQUALS, condition: %s }
            ] }
          }) {
            collection { id handle }
            userErrors { field message }
          }
        }
        """ % (json.dumps(v), json.dumps(handle), json.dumps(v)), mutation=True)

        errs = result["collectionCreate"]["userErrors"]
        if errs:
            print(f"  warning: {handle}: {errs}")
            continue

        gid = result["collectionCreate"]["collection"]["id"]

        # A collection created through the API is published to nothing, so it
        # 404s on the storefront until this runs. Learned the hard way with the
        # price bands.
        if not pubs:
            unpublished.append(handle)
            print(f"  created {handle}  (NOT PUBLISHED)")
            continue

        inputs = ", ".join('{publicationId: "%s"}' % p for p in pubs)
        pub = gql("""
        mutation {
          publishablePublish(id: "%s", input: [%s]) { userErrors { message } }
        }
        """ % (gid, inputs), mutation=True)
        perrs = pub["publishablePublish"]["userErrors"]
        if perrs:
            unpublished.append(handle)
        print(f"  created {handle}" + (f" (publish warning: {perrs})" if perrs else ""))

    print(f"\nCreated {len(missing)} collection(s).")

    if unpublished:
        # Exit non-zero so a scheduled run shows up as failed rather than
        # green. A collection nobody can reach is a silent gap in navigation.
        print(f"\n{len(unpublished)} collection(s) are NOT published and will 404:")
        for h in unpublished:
            print(f"  - {h}")
        print("\nPublish them in the Shopify admin, or grant the app\n"
              "read_publications + write_publications and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
