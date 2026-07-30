# Where things stand

Snapshot at the end of the second session, 30 July 2026. Written so tomorrow
starts from facts rather than from re-reading commits.

## Live right now

**theyoink.com** — public, SSL, no password. Shopify store `9wgxci-qu`.

Homepage, in order: **Yoink of the Day** (inline variant picker and add-to-cart,
real countdown, % claimed bar) → **Shop by price** (5 bands) → **Shop by
category** → **Add these to your order** → **Recent Yoinks** (greyed, ENDED
stamped with the discount it ran at, "Bring back this deal").

Announcement bar names today's Yoink and links to it. Cart is a drawer and opens
automatically on add. Footer carries the real Facebook and Instagram links.

**theyoink-app.fly.dev** — embedded admin app, deploy version 14. Two Fly
machines: the web server and an always-on scheduler.

## Two repos, plus one that is only local

| Repo | Local | What |
|---|---|---|
| `afbohn/project-aj` | `theme/` | The Shopify theme. Synced two-way; **every push deploys.** |
| `afbohn/theyoink-meta` | `meta-app/` | Instagram/Facebook daily-deal poster. Built, gated off. |
| — | `theyoink-app/` | The admin app. Git repo with **no remote**; ships by `fly deploy`. |

`theyoink-app/` having no remote is worth remembering: committing there backs up
nothing. It exists on this laptop and on Fly.

## The first unattended activation worked

30 July, 14:00 UTC. Verified rather than assumed:

- **Luxe Australian Sateen Sheet Set** priced at **$239.94 from $279.00**, 14% off
- `price_snapshot` written, recording `compare_at: null` on the original — so the
  app *added* a compare-at rather than overwriting a supplier MSRP, which is the
  rule working on its first real run
- Storefront showed the MSRP struck through, countdown running, 3% claimed
- The previous deal (Mini Blossom Bowl) swept correctly
- Both heartbeats `ok`

One thing that run taught us: **the heartbeat detail cannot tell you an
activation happened.** It is upserted per job, so the last run wins, and a run
that only swept reads `swept 1` whether or not the morning's activation
succeeded. To confirm an activation you have to look at the deal itself.

## The deal pipeline

Everything that changes a price lives in the app, once, in
`app/lib/pricing.server.ts`. Two guarantees, both learned by finding the bug:

- **Never below cost.** Storefront Liquid cannot read unit cost, so the floor is
  applied wherever the write happens. A product missing cost on any variant is
  refused rather than guessed at.
- **Never destroy a supplier MSRP.** Compare-at is written only where there was
  none, and the snapshot records both fields so expiry restores them exactly.

The scheduler (`scheduler.mjs`, its own Fly machine) calls:

- `/cron/lifecycle` every 15 min — activate what is due, restore what has ended
- `/cron/catalog` every 30 min — price-band tags, vendor collections, sold-out sweep

## Sold-out products come off the storefront

New this session, live since 30 July. `/cron/catalog` unpublishes products that
have sold out and republishes them when stock returns.

- **Unpublishing, not tagging.** A tag plus a collection rule hides a product
  from the bands and categories and nothing else — it stays in search, in
  `/collections/all` (which the homepage cross-sell reads), and in the sitemap.
- **Two consecutive zero readings before acting.** Collective's sync blips to
  zero; acting on the first reading makes products flicker in and out of the
  sitemap every half hour. First reading writes `oos-pending`; second writes
  `oos` and unpublishes.
- **The live deal and anything queued within 7 days is never touched.**
- **`oos` is the permission slip for republishing.** A product unpublished by
  hand carries no tag, so this never resurrects it.

First run marked **42 of 1150** products pending. Expect a standing population of
a few percent. The catalog job now takes ~24s rather than ~3s; that is the
per-variant sellability check, and it is expected.

## What to check next session

1. **The sold-out sweep's steady state.** Confirm the count is not drifting
   upward, and that products which come back in stock actually reappear. The
   cron summary reports `N hidden`, `N restored` and `N pending removal`.
2. **Click "Bring back this deal"** on a Recent Yoink and confirm the count
   increments. Still never clicked by a human.
3. **Which Collective returns policy the store is on.** See *Returns* below —
   this is the last genuinely unknown thing, and it sets the margin floors.

## Known gaps

- **Category tags are Python-only.** `catalog.server.ts` does bands and vendors.
  It does **not** write `cat-*` tags — `scripts/categories.py` does, via GitHub
  Actions. So **disabling those workflows would silently stop new products
  appearing in Shop by Category.** Port `categories.py` into the app before
  switching them off. (An earlier version of this document wrongly claimed the
  cron already did this.)
- **Python still holds a duplicate of the pricing logic** (`theme/scripts/deal.py`).
  The app path has now survived a real unattended activation, so this can go —
  keep the read-only commands as a CLI.
- **GitHub Actions workflows are still enabled** in the theme repo. Harmless, but
  see the category-tag warning above before disabling them.
- **The app has no test harness.** Verification is by driving exported functions
  with a stubbed admin, which works but is ad hoc.
- **No brand.** Logo, colours and fonts are theme settings waiting on Jake. Spec
  is in `docs/brand-asset-spec.md`.
- **SPF and DKIM not set.** SPF missing entirely; DKIM needs a 1024-bit key from
  Google Workspace because Shopify's DNS field caps at 255 characters.
- **Judge.me is installed** and its embed active, but no review UI is wired into
  product cards or the product page.
- **Meta posting is gated off.** Set repository variable `POSTING_ENABLED=true`
  in `theyoink-meta` when there is a logo worth posting under.
- **Test deals pollute Recent Yoinks.** Several predate `deal_price`.
- **The category URL still says tobacco.** The title now reads "Food &
  Beverages", but the handle is `cat-food-beverages-tobacco`. Changing it means
  retagging all 41 products, because the collection rule matches `tag == handle`.

## Returns, and what it means for discounts

Answered this session, except for one thing you have to look up in the admin.

Shopify Collective's **default** returns policy for retailers who joined after
10 December 2024: supplier creates the return label, 2-day processing, 30-day
window, no label fee, no restocking fee, declined returns auto-cancel, refunds
auto-refund. Retailers who joined **before** that date have a legacy default of
*no action taken*, which is a completely different risk profile. **Check which
one this store is on** — Collective app → Settings → Policies.

Three things that are structural and cannot be fixed by policy wording:

1. **You carry the customer-facing liability.** If a supplier does not refund an
   accepted return, the return does not auto-close and you must refund the
   customer yourself and chase the supplier separately.
2. **One returns policy for the whole store**, and supplier policies are not
   visible in the Collective app. So the published policy has to be the most
   restrictive common denominator across every supplier, or you eat the gap.
3. **Overriding shipping rates does not reduce what you owe.** Customers see
   supplier rates unless you build a custom Collective shipping profile, and if
   you override to show a nicer rate you still pay the supplier theirs.

**So deep discounts on expensive items are reckless.** Deal prices clamp to cost,
so at maximum discount the gross margin on that unit is near zero — and then any
return cost at all (label fee, restocking fee, partial supplier refund) is a
straight loss on a unit that never made money. Cap discount by price band, and
do not run a deep Yoink on a supplier's expensive SKUs without confirmed
full-refund terms in writing.

## Things that bit us, so they don't again

- **`sections/*-group.json` is owned by the theme editor.** Repo edits are
  silently ignored. Section liquid syncs reliably; section-group JSON does not.
- **Shopify's client-credentials token expires in 24 hours.** Store the client id
  and secret and mint a token per run.
- **`metaobject.system.id` in Liquid is numeric, not a gid.**
- **Decimal metafields make Liquid division float.** Round explicitly.
- **API-created collections are published to nothing** and 404 until published.
- **Shopify price rules match ANY variant** while the card shows the LOWEST, so
  price bands are computed from minimum variant price and written as tags.
- **A truncated candidate pool destroys variety.** The pool is interleaved by
  vendor and covers the whole catalogue.
- **`tag:oos` also matches `oos-pending`.** Shopify's search tokenizes on
  hyphens, so tag queries cannot distinguish the two. Read the `tags` array
  instead of trusting a `tag:` query.
- **Liquid's `image_tag` cannot take a hyphenated named argument.** No
  `data-foo:` — put the attribute on a wrapping element instead.
- **`totalInventory` does not mean "unsellable".** A variant with tracking off or
  an inventory policy of CONTINUE sells at zero. Availability has to be settled
  per variant.
- **The 0%-discount trap.** A queued deal with `discount_percent: 0` used to be
  rejected before the target-margin block ever ran, producing no Yoink at all
  for that day. Fixed — a margin target is now enough on its own — but the shape
  is worth remembering: a guard that runs before the fallback it guards.

## Next session, first thing

**"Also on sale" section.** The homepage cross-sell shows arbitrary products from
`all`. It should show other genuinely discounted products, excluding that day's
Yoink.

Earlier notes said Shopify rejects the obvious approach. That is true of the
**admin UI**, but the Admin API enum `CollectionRuleColumn` includes
**`IS_PRICE_REDUCED`**, which matches exactly this. Try creating the collection
through the API — the same way `catalog.server.ts` creates vendor collections —
before building a tag-based path.

The cross-sell also needs to exclude the live deal's product, which it does not
today (it only excludes `closest.product`, nil on the homepage).
