#!/usr/bin/env python3
"""
Assign price-band tags to every product, based on the price a shopper sees.

WHY TAGS AND NOT A PRICE RULE. Shopify's automated collections can filter on
VARIANT_PRICE, but that rule matches if ANY variant falls in range, while the
product card displays the LOWEST variant price. On a catalog with multi-packs
that combination is actively misleading: "Artisan Soup Mugs" runs $36 to $125,
so a VARIANT_PRICE rule files it under "$50 and up" where its card then reads
$36. Six of the eight products in that band displayed a sub-$50 price.

So we compute the band from the minimum variant price — the number actually on
the card — write it as a tag, and let the collections match the tag. Bands come
out exact and non-overlapping, and every card shows a price inside its band.

Re-run this after importing products or changing prices. It is idempotent:
stale band tags are removed, so a product that moves bands ends up with exactly
one, and a product already correct is left alone.

    python3 scripts/bands.py --dry-run
    python3 scripts/bands.py
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from decimal import Decimal

TAG_PREFIX = "band-"

# (tag suffix, lower bound inclusive, upper bound exclusive or None)
BANDS = [
    ("under-10", Decimal("0"),  Decimal("10")),
    ("10-20",    Decimal("10"), Decimal("20")),
    ("20-30",    Decimal("20"), Decimal("30")),
    ("30-50",    Decimal("30"), Decimal("50")),
    ("50-up",    Decimal("50"), None),
]


from shopify_auth import gql  # noqa: E402  (see module docstring for auth order)


def band_for(price):
    for suffix, lo, hi in BANDS:
        if price >= lo and (hi is None or price < hi):
            return TAG_PREFIX + suffix
    return None


def fetch_all_products():
    """Page through the catalog. Dropship catalogues grow fast, so don't assume
    everything fits in one page."""
    products, cursor = [], None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = gql("""
        {
          products(first: 100%s) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              title
              tags
              priceRangeV2 { minVariantPrice { amount } }
            }
          }
        }
        """ % after)
        page = data["products"]
        products.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return products
        cursor = page["pageInfo"]["endCursor"]


def main():
    ap = argparse.ArgumentParser(description="Tag products with their price band.")
    ap.add_argument("--dry-run", action="store_true", help="report changes without making them")
    args = ap.parse_args()

    products = fetch_all_products()
    print(f"{len(products)} products\n")

    changes = []
    for p in products:
        price = Decimal(p["priceRangeV2"]["minVariantPrice"]["amount"])
        want = band_for(price)
        have = {t for t in p["tags"] if t.startswith(TAG_PREFIX)}

        if want is None:
            continue
        if have == {want}:
            continue

        changes.append({
            "id": p["id"],
            "title": p["title"],
            "price": price,
            "add": want if want not in have else None,
            "remove": sorted(have - {want}),
        })

    if not changes:
        print("Every product already carries the right band tag. Nothing to do.")
        return

    print(f"{'PRODUCT':44} {'MIN':>8}  CHANGE")
    print("-" * 84)
    for c in changes:
        bits = []
        if c["add"]:
            bits.append(f"+{c['add']}")
        if c["remove"]:
            bits.append(" ".join(f"-{t}" for t in c["remove"]))
        print(f"{c['title'][:43]:44} {c['price']:>8}  {'  '.join(bits)}")

    if args.dry_run:
        print(f"\nDry run — {len(changes)} product(s) would change. Nothing was written.")
        return

    print()
    for c in changes:
        if c["remove"]:
            tags = ", ".join(f'"{t}"' for t in c["remove"])
            res = gql('mutation { tagsRemove(id: "%s", tags: [%s]) '
                      '{ userErrors { message } } }' % (c["id"], tags), mutation=True)
            errs = res["tagsRemove"]["userErrors"]
            if errs:
                print(f"  warning: {c['title'][:40]}: {errs}")
        if c["add"]:
            res = gql('mutation { tagsAdd(id: "%s", tags: ["%s"]) '
                      '{ userErrors { message } } }' % (c["id"], c["add"]), mutation=True)
            errs = res["tagsAdd"]["userErrors"]
            if errs:
                print(f"  warning: {c['title'][:40]}: {errs}")

    print(f"Updated {len(changes)} product(s).")
    print("\nCollections match on these tags, so they will catch up within a minute.")


if __name__ == "__main__":
    main()
