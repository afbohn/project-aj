# Where things stand

Snapshot at the end of the first build session. Written so tomorrow starts from
facts rather than from re-reading commits.

## Live right now

**theyoink.com** — public, SSL, no password. Shopify store `9wgxci-qu`.

Homepage, in order: **Yoink of the Day** (inline variant picker and add-to-cart,
real countdown, % claimed bar) → **Shop by price** (5 bands) → **Shop by
category** (15 groups from Shopify's standard taxonomy) → **Add these to your
order** → **Recent Yoinks** (greyed, ENDED stamped across the image with the
discount it ran at, discounted vs regular price, "Bring back this deal").

Announcement bar names today's Yoink and links to it, rotating on its own.
Cart is a drawer and opens automatically on add. Footer carries the real
Facebook and Instagram links.

**theyoink-app.fly.dev** — embedded admin app. Two Fly machines: the web server
and an always-on scheduler.

## Two repos

| Repo | Local | What |
|---|---|---|
| `afbohn/project-aj` | `theme/` | The Shopify theme. Synced two-way with the live theme; **every push deploys.** |
| `afbohn/theyoink-meta` | `meta-app/` | Instagram/Facebook daily-deal poster. Built, gated off. |

`theyoink-app/` is the admin app. Deployed to Fly; not on GitHub.

## The deal pipeline

Everything that changes a price lives in the app, once, in
`app/lib/pricing.server.ts`. Two guarantees, both learned by finding the bug:

- **Never below cost.** Storefront Liquid cannot read unit cost, so the floor is
  applied wherever the write happens. A product missing cost on any variant is
  refused rather than guessed at.
- **Never destroy a supplier MSRP.** Several suppliers sync a real one. Compare-at
  is written only where there was none, and the snapshot records both fields so
  expiry restores them exactly.

The scheduler (`scheduler.mjs`, its own Fly machine) calls two endpoints:

- `/cron/lifecycle` every 15 min — activate what is due, restore what has ended
- `/cron/catalog` every 30 min — price-band tags, category tags, vendor collections

Both write heartbeats the dashboard reads. **A stale heartbeat is the alarm**,
because both failure modes are otherwise silent: activation stopping shows a
countdown beside a full price, sweeping stopping keeps an ended deal discounted.

## What to check tomorrow, in order

1. **The 9am Central activation.** A week is scheduled — Italic sheets Thu,
   Panama Hat Fri, then prodigalpottery, Goal Five, Bigalli, White Water Life,
   Blackline, Navigate Craft. Thursday 9am is the first unattended run of the
   consolidated path. Dashboard should show it priced with a snapshot and a real margin, the
   storefront should show the MSRP struck through, and the heartbeat should be
   green with a recent run.

   One to watch: the Monday deal (Panama Hat Australian Outdoor) is queued at
   **0% discount**, which will price it at its current price and show no saving.
   Worth fixing or dropping before Monday.
2. **Click add-to-cart on the Yoink** and confirm the drawer opens with the right
   variant, and that the upsell inside suggests same-supplier items.
3. **Click "Bring back this deal"** on a Recent Yoink and confirm the count
   increments. The endpoint was fixed late and has not been clicked by a human.

## Known gaps

- **Python still holds a duplicate of the pricing logic** (`theme/scripts/deal.py`).
  Kept deliberately as a fallback until the app path survives one real
  activation. Delete after that, keeping the read-only commands as a CLI.
- **GitHub Actions workflows are still enabled** in the theme repo and duplicate
  the app's jobs. Harmless — both are idempotent and skip work the other did —
  but they should be disabled once the app path is proven.
- **Test deals pollute Recent Yoinks.** Several were created before `deal_price`
  existed, so they show no discounted price. Real deals will.
- **No brand.** Logo, colours and fonts are theme settings waiting on Jake. Spec
  is in `docs/brand-asset-spec.md`.
- **SPF and DKIM not set.** SPF is missing entirely; DKIM needs a 1024-bit key
  from Google Workspace because Shopify's DNS field caps at 255 characters.
- **Judge.me is installed** and its app embed is active, but no review UI is
  wired into product cards or the product page.
- **Collection filters** are configured in the Search & Discovery app, not in
  code. Products now carry `cat-*` and `band-*` tags worth exposing there.
- **Meta posting is gated off.** Set the repository variable
  `POSTING_ENABLED=true` in `theyoink-meta` when there is a logo worth posting
  under; until then the job previews daily and publishes nothing.
- **Returns policy unknown.** Whether Collective suppliers credit a return
  determines whether deep discounts on expensive items are smart or reckless.
  Worth asking them — it changes the margin floors.

## Next session, first thing

**"Also on sale" section.** The homepage cross-sell currently shows arbitrary
products from `all`. It should show other genuinely discounted products,
excluding that day's Yoink. Shopify REJECTS the obvious approach — a rule of
"compare at price is set" comes back with *"You can't set the condition Compare
at price is set"* — so it needs an `on-sale` tag written by the catalogue sync
wherever compare-at exceeds price, plus a collection matching that tag. Same
shape as the price bands, and for the same reason: Shopify's native price rules
cannot express what we need.

The cross-sell section will also need to exclude the live deal's product, which
it does not today (it only excludes `closest.product`, which is nil on the
homepage).

## Things that bit us, so they don't again

- **`sections/*-group.json` is owned by the theme editor.** Repo edits to
  `header-group.json` were committed, pushed, and silently ignored. Section
  liquid syncs reliably; section-group JSON does not.
- **Shopify's client-credentials token expires in 24 hours.** Store the client id
  and secret and mint a token per run; a token pasted into a secret works today
  and dies tomorrow.
- **`metaobject.system.id` in Liquid is numeric, not a gid.** Cost a silent 400
  on every vote.
- **Decimal metafields make Liquid division float.** Rendered
  "37.30569948186528% off" live. Round explicitly.
- **API-created collections are published to nothing** and 404 until explicitly
  published.
- **Shopify price rules match ANY variant** while the card shows the LOWEST, so
  price bands are computed from minimum variant price and written as tags.
- **A truncated candidate pool destroys variety.** Ranking by discount and taking
  the top 80 collapsed 18 suppliers to 3. The pool is now interleaved by vendor
  and covers the whole catalogue.
