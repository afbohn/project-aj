#!/usr/bin/env python3
"""
Tag products with their top-level Shopify category, and keep a collection per
category.

WHY CATEGORY AND NOT VENDOR. Browsing by supplier name invites a shopper to
search that supplier and buy direct — on a dropship catalogue that is handing
away the sale. Category is the axis that keeps them here.

WHY THE STANDARD TAXONOMY AND NOT productType. Suppliers fill productType with
whatever they like ("Ceramic" across a third of the catalogue). Shopify's
standard category is a real hierarchy and is populated on 92% of this catalogue,
so the first segment of it — Home & Garden, Apparel & Accessories — is a clean,
shopper-facing grouping we did not have to invent.

Only the TOP level is used. The full paths run five deep
("Apparel & Accessories > Clothing Accessories > Hats > Fedoras"), which is
precise and useless as navigation.

    python3 scripts/categories.py --dry-run
    python3 scripts/categories.py
"""

import argparse
import json
import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))

from shopify_auth import gql  # noqa: E402

PREFIX = "cat-"

# Shopify's taxonomy names segments for completeness, not for shop windows.
# "Food, Beverages & Tobacco" is the real top-level segment even when nothing in
# it is tobacco, and putting that word on a card on the homepage advertises
# something we do not sell. The tag and the handle still follow the taxonomy —
# only the shopper-facing title is overridden, so retagging stays mechanical.
#
# Keyed by taxonomy segment. Add a line here when a segment reads badly.
DISPLAY_NAMES = {
    "Food, Beverages & Tobacco": "Food & Beverages",
}


def display_name(top):
    return DISPLAY_NAMES.get(top, top)


def handleize(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch_products():
    products, cursor = [], None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = gql("""
        {
          products(first: 250%s, query: "status:active") {
            pageInfo { hasNextPage endCursor }
            nodes { id title tags category { fullName } }
          }
        }
        """ % after)
        page = data["products"]
        products.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return products
        cursor = page["pageInfo"]["endCursor"]


def fetch_collections():
    """handle -> {id, title}. Title is carried so a renamed category can be
    corrected in place rather than only at creation."""
    out, cursor = {}, None
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
            out[n["handle"]] = {"id": n["id"], "title": n["title"]}
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def publication_ids():
    try:
        data = gql("{ publications(first: 10) { nodes { id name } } }")
    except SystemExit:
        return []
    wanted = {"Online Store", "Shop"}
    return [n["id"] for n in data["publications"]["nodes"] if n["name"] in wanted]


def main():
    ap = argparse.ArgumentParser(description="Tag products by top-level category.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    products = fetch_products()
    top_levels = {}
    changes = []
    no_category = 0

    for p in products:
        full = (p.get("category") or {}).get("fullName")
        if not full:
            no_category += 1
            continue
        top = full.split(" > ")[0].strip()
        want = PREFIX + handleize(top)
        top_levels[top] = want

        have = {t for t in p["tags"] if t.startswith(PREFIX)}
        if have == {want}:
            continue
        changes.append({"id": p["id"], "title": p["title"], "add": want,
                        "remove": sorted(have - {want})})

    print(f"\n{len(products)} products | {len(top_levels)} categories | "
          f"{no_category} without a category\n")
    for top, tag in sorted(top_levels.items()):
        shown = display_name(top)
        # Flag overridden names so a dry run shows what a shopper will read,
        # not just what the taxonomy calls it.
        suffix = f"   (shown as {shown!r})" if shown != top else ""
        print(f"  {tag:28} {top}{suffix}")

    if changes:
        print(f"\n{len(changes)} product(s) need retagging")
    if args.dry_run:
        print("\nDry run. Nothing written.")
        return

    for c in changes:
        if c["remove"]:
            tags = ", ".join(f'"{t}"' for t in c["remove"])
            gql('mutation { tagsRemove(id: "%s", tags: [%s]) { userErrors { message } } }'
                % (c["id"], tags), mutation=True)
        gql('mutation { tagsAdd(id: "%s", tags: ["%s"]) { userErrors { message } } }'
            % (c["id"], c["add"]), mutation=True)
    print(f"\nRetagged {len(changes)} product(s).")

    existing = fetch_collections()

    # Correct any category whose shopper-facing title has drifted from
    # DISPLAY_NAMES. Runs before creation so a rename lands even when there is
    # nothing new to create.
    for top, handle in sorted(top_levels.items()):
        current = existing.get(handle)
        want_title = display_name(top)
        if not current or current["title"] == want_title:
            continue
        gql('mutation { collectionUpdate(input: {id: "%s", title: %s}) '
            '{ userErrors { message } } }' % (current["id"], json.dumps(want_title)),
            mutation=True)
        print(f"  renamed {handle}: {current['title']!r} -> {want_title!r}")

    missing = {t: h for t, h in top_levels.items() if h not in existing}
    if not missing:
        print("Every category already has a collection.")
        return

    pubs = publication_ids()
    for top, handle in sorted(missing.items()):
        res = gql("""
        mutation {
          collectionCreate(input: {
            title: %s,
            handle: %s,
            sortOrder: BEST_SELLING,
            ruleSet: { appliedDisjunctively: false, rules: [
              { column: TAG, relation: EQUALS, condition: %s }
            ] }
          }) { collection { id } userErrors { message } }
        }
        """ % (json.dumps(display_name(top)), json.dumps(handle), json.dumps(handle)),
            mutation=True)
        errs = res["collectionCreate"]["userErrors"]
        if errs:
            print(f"  warning {handle}: {errs}")
            continue
        gid = res["collectionCreate"]["collection"]["id"]
        if pubs:
            inputs = ", ".join('{publicationId: "%s"}' % p for p in pubs)
            gql('mutation { publishablePublish(id: "%s", input: [%s]) { userErrors { message } } }'
                % (gid, inputs), mutation=True)
        print(f"  created {handle}")


if __name__ == "__main__":
    main()
