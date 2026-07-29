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
import subprocess
import sys
import urllib.error
import urllib.request

STORE = "9wgxci-qu.myshopify.com"
API_VERSION = "2025-07"
PREFIX = "vendor-"


def gql(query, mutation=False):
    token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    if token:
        req = urllib.request.Request(
            f"https://{STORE}/admin/api/{API_VERSION}/graphql.json",
            data=json.dumps({"query": query}).encode(),
            headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.URLError as exc:
            sys.exit(f"Admin API request failed: {exc}")
        if "errors" in payload:
            sys.exit(f"Admin API errors: {payload['errors']}")
        return payload.get("data", {})

    cmd = ["shopify", "store", "execute", "-s", STORE, "--json", "-q", query]
    if mutation:
        cmd.append("--allow-mutations")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout
    if "{" not in out:
        sys.exit(f"Shopify CLI returned no data.\n{out}\n{proc.stderr}")
    try:
        return json.loads(out[out.index("{"):])
    except json.JSONDecodeError:
        sys.exit(f"Could not parse response:\n{out[:1500]}")


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
    data = gql("{ publications(first: 10) { nodes { id name } } }")
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
        inputs = ", ".join('{publicationId: "%s"}' % p for p in pubs)
        pub = gql("""
        mutation {
          publishablePublish(id: "%s", input: [%s]) { userErrors { message } }
        }
        """ % (gid, inputs), mutation=True)
        perrs = pub["publishablePublish"]["userErrors"]
        print(f"  created {handle}" + (f" (publish warning: {perrs})" if perrs else ""))

    print(f"\nCreated {len(missing)} collection(s).")


if __name__ == "__main__":
    main()
