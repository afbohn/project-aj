# Where things stand

Snapshot at the end of 31 July 2026. Written so tomorrow starts from facts
rather than from re-reading commits.

## Live right now

**theyoink.com** — public, SSL, no password. Shopify store `9wgxci-qu`.

Homepage, in order: **Yoink of the Day** → **The Bargain Bin** → **Shop by
price** → **Shop by category** → **Recent Yoinks**. The old "Add these to your
order" cross-sell was removed; its section file remains, only its placement
went.

**theyoink-app.fly.dev** — the admin app, and now the control plane for
everything. Two Fly machines: the web server and an always-on scheduler.

**Instagram @shoptheyoink and the Facebook Page** — both live, both posting
through the app. The teaser campaign has started.

## Three repos, all on GitHub

| Repo | Local | What |
|---|---|---|
| `afbohn/project-aj` | `theme/` | The Shopify theme. **Every push deploys.** |
| `afbohn/theyoink-app` | `theyoink-app/` | The admin app and every agent. Ships by `fly deploy`. Private. |
| `afbohn/theyoink-meta` | `meta-app/` | **Retired.** Ported into the app; its workflow is disabled. |

`theyoink-app` was laptop-only until today. It is now backed up, which matters
more than it did before, because it is where all eight agents live.

## The eight agents

All visible at **`/app/agents`** with health, last-run age, "Run now", and pause
where pausing is safe.

| Agent | Every | Does | Pausable |
|---|---|---|---|
| `lifecycle` | 15 min | Activates the Yoink, restores the price when it ends | No |
| `catalog` | 30 min | Price bands, categories, vendor collections, sold-out sweep | No |
| `bargain-bin` | 60 min | Rotates the weekly bin | Yes |
| `invariants` | 30 min | Asserts what must be true across agents. Changes nothing | No |
| `meta` | 60 min | Posts the Yoink of the Day | Yes — **currently paused** |
| `teaser` | 60 min | Works the teaser queue, one a day | Yes — **currently on** |
| `enrich` | Daily | Tags and scores the catalogue with a model | Yes — **currently on** |
| `shipping` | 30 min | Measures what each supplier and product costs to ship | Yes — **currently on** |

**The lifecycle and catalogue sweep have no pause button on purpose.** Both fail
silently and expensively when they stop, and an off switch someone forgets to
flip back is exactly how that happens. Stopping them is a deploy.

**`meta` is paused deliberately.** Turning it on now would post a full product ad
immediately after "WHAT IS THE YOINK?", killing the teaser campaign. Switch it on
when the teasers run out and the brand lands.

Agent switches live in Shopify metaobjects, not environment variables, so pausing
is a click rather than a CLI and a restart. Env vars are still read as a fallback
for an agent nobody has toggled.

## Pages in the app

- **`/app`** — deal queue, calendar, exposure, performance
- **`/app/agents`** — every scheduled job, health, run now, pause
- **`/app/bargain-bin`** — members, % off, cash kept per unit, rotate
- **`/app/social`** — today's deal post, teaser queue with live validation, and
  what the posts did
- **`/app/ads`** — campaign creative, spend, ROAS, CPC, and an AI read on it.
  Everything it creates is **PAUSED**; going live is a human click, asserted by
  reading the object back after every create.

The dashboard also carries **"Asked to come back"** — expired Yoinks ranked by
storefront "bring this back" votes, next to what they ran at and made per unit.
Demand for a product whose margin work is already done is the cheapest input to
what tomorrow's deal should be. It renders nothing when nobody has voted.

## The Bargain Bin

Weekly rotating collection, **exactly 25% off, never more**, only on products
that stay profitable at that discount.

- Margin measured on the **worst variant**, floor 20% after the discount.
- **Products carrying a supplier MSRP are excluded outright.** We never overwrite
  a real list price, so the saving would be measured against that MSRP and show
  as more than 25% — one product showed 43% in the first live week. Costs about a
  third of the pool (564 → 382) and keeps all twelve vendors, nine distinct weeks.
- **Selection interleaves by vendor.** One supplier is 54% of the pool; ranked by
  margin the bin comes out 2 vendors and 90% one maker.
- Nothing in this catalogue survives a 35% margin floor at 25% off, so 25% is
  near what this supplier mix can bear.

The live week is 5 vendors rather than 12 because a forced rotation excluded the
previous week's members, which held the thin suppliers' only eligible products.
**It self-corrects at the 6 August rotation.**

## Social

Ported out of Python and GitHub Actions into the app on 30 July.

- **Deal captions: figures composed, language written.** Every number is read
  from Shopify — the caption cannot advertise a price the product does not have.
  The voice lines around them assert nothing, so flavour cannot be false.
- **Teasers are checked, not composed.** Having no product behind them, they are
  refused if they contain a price, a percentage, a countdown, a was/now
  comparison or a delivery promise. The check runs in the browser as you type and
  again at publish, using the same function.
- **The queue and the log are one record at two points in its life**, so they
  cannot disagree about what has gone out.
- **Links carry UTM tags.** `utm_medium=social` (organic), `utm_source` is the
  platform, `utm_campaign=yoink-YYYY-MM-DD`, `utm_content` the product handle.
  Captions are composed per platform so Instagram and Facebook can be told apart.

Teaser campaign: nine cards, type on a flat colour field, generated by
`meta-app/make_teasers.py` and served from `theme/assets/teaser-*.png`. `q1`
posted 30 July to both platforms. One a day thereafter.

## Catalogue enrichment

A model reads each product and writes curation signal: occasion, recipient,
setting, stated attributes, colours, and a 1-5 **hero score** for how well it
would carry a day as the Yoink.

Skipped by content hash, so daily costs almost nothing after the first pass.
**The hash includes `PROMPT_VERSION`** — without that, improving the prompt
improved nothing, because every already-enriched product matched its old hash
and was skipped forever.

`hero_score` and `color` are **definition-backed metafields**, not keys in the
JSON blob. A JSON metafield reaches the Storefront API as an opaque string, so
Search & Discovery and the chatbot could never have used them. Both carry
`smartCollectionCondition` and `adminFilterable`, storefront `PUBLIC_READ`. The
blob keeps the narrative fields nothing queries — angle, heroReason, enrichedAt.

Occasions/recipients/settings stay as `e-` tags; those already drive collections
and filters. Colour does not — it is a value, ~7% of products state one, and the
rare-tag sweep would have deleted it.

Coverage at end of 30 July: hero_score on 480 of 1,294, colour on 143.
Distribution 1:22 2:167 3:231 4:58 5:2. Variety packs score highest, which is a
real signal — a bundle photographs well and needs no explaining.

Two guards worth keeping: banned universal occasions (`gift` was on 42% of the
catalogue, `housewarming` 52% — a tag on half the catalogue is not a filter),
and a sweep of tags on fewer than three products, which cannot group anything.

## Categories — complete as of 31 July

**1,399 of 1,400 published products carry a Shopify taxonomy category**, so
Shop by Category reaches all of them. It was 1,257 that morning.

143 had none, concentrated in four suppliers: ISlide (48, the whole vendor),
Sweet Bamboo (35), prodigalpottery (12), White Water Life (10).

**Filled from `productType`, not from the vendor's modal category.** Modal-fill
was the obvious approach and would have been wrong for most: Sweet Bamboo's
modal covers 23% of its products and prodigalpottery's 21%, so the mode is a
minority. `productType` — "Vacation Slides", "Footies", "Ceramic", "Polos" — is
the reliable signal, and where a vendor already had categorised products their
exact taxonomy ids were reused rather than resolved by search.

The one left uncategorised is **Shipping Protection**, the UpCart add-on. It is
a service rather than a product: no category, no shipping rate, and correctly
neither.

**It stays complete on its own now.** The catalogue agent applies a
`category_rule` metaobject — vendor + productType to taxonomy id — to any
product whose supplier set no category. The 73 rules were derived FROM the
catalogue, from combinations where the already-categorised products agree, so
the agent propagates a decision already made rather than guessing. A new ISlide
product inherits Sandals because every other ISlide product is Sandals.

A rule needs at least two agreeing examples, so a lone oddity never becomes one.
That is why seven products still have no category: single-product vendors with
nothing to learn from. Adding a rule by hand is one metaobject entry.

## The Yoink is now visible outside the metaobject

The deal lived only in a `daily_deal` metaobject, which Liquid and the Admin API
can read and almost nothing else can — the Storefront API returns a metaobject
reference as an opaque gid with no way to dereference it. The support chatbot,
Search & Discovery and any future integration were structurally blind to it.

There is now a `yoink-of-the-day` tag and an automated collection on it,
**reconciled** against live deals on every lifecycle run rather than written on
activate and cleared on sweep — two places that drift the first time a window is
edited by hand.

## What to check next session

1. **7 August has no Yoink.** Its deal was removed because the product turned
   out to be unshippable — see below. The rest run to 7 August, and nothing is
   being promoted yet, so an empty day is a non-event rather than urgent.
2. **The Fidget Games** — 22 products unpublished and tagged `no-ship-rate`
   because Shopify offers no shipping rate for them, so checkout dead-ended.
   Needs raising with the supplier; nobody else can fix it.
3. **Deals run out 8 August.** Nothing is queued past it, and the homepage
   section simply hides itself on a day with nothing scheduled.
2. **The 6 August bin rotation** — vendor spread should return to twelve.
3. **Enrichment coverage** should reach the full 1,294 within a few runs at 350
   per run. Until it does, a missing hero score means "not scored yet", never
   "bad product".
4. **The teaser cadence** — one a day, `q2` onward, at `/app/social`.
5. **Whether `hello@theyoink.com` actually receives mail.** It is now published
   on two public profiles.

## Known gaps

- **The Meta token can spend money.** It carries `ads_management`, deliberately,
  because the ads agent will use this same token. See *decisions.md* — this
  reverses an earlier decision and moves a safeguard from the token to the code
  that has not been written yet.
- **The shipping policy page is still unpublished.** Everything else is live.
- **Search & Discovery filters are not wired to the new metafields.** The
  definitions are filterable; making a filter appear is a manual step in the
  Search & Discovery app.
- **21% of the catalogue costs more than 35% of its price to ship.** Excluded
  from every deal surface automatically; still listed. Deferred, not rejected.
- **The Fidget Games has 22 unpublished products** tagged `no-ship-rate`. They
  return no shipping rate at all, so they could not be bought. Needs the
  supplier to fix their rate configuration.
- **`enrich.color` and `enrich.hero_score` are typed metafields now**, but the
  bin, candidates and theme only use hero_score. Colour is unused.
- **`ship.cost` is missing on ~100 products** — 24 genuinely have no rate, the
  rest are recent arrivals the sweep has not reached. Absence is a real state,
  distinct from zero.
- **The Instagram bio is not set.** There is no API for it — profile fields are
  editable only in the app or Business Suite. The Facebook Page is done.
- **`theme/scripts/deal.py` still duplicates the pricing logic.** The app path has
  survived a real unattended activation, so it can go; keep the read-only
  commands as a CLI.
- **No brand.** Logo, colours and fonts are theme settings waiting on Jake.
- **Judge.me is installed** but no review UI is wired into cards or the PDP.
- **The `meta` heartbeat is red from a run at 16:43 on 30 July**, one minute
  before the agent was paused. It is stale, not ongoing — but `/app/agents`
  will show a red light until the agent runs successfully again, which is the
  kind of thing that teaches you to stop reading the dashboard.
- **The category URL still says tobacco.** The title reads "Food & Beverages";
  the handle is `cat-food-beverages-tobacco`. Changing it means retagging 41
  products, because the collection rule matches `tag == handle`.
- **The app has no test harness.** Verification is by driving exported functions
  with a stubbed admin, which works but is ad hoc.

**Email is done.** MX to Google Workspace, SPF (`v=spf1 include:_spf.google.com
~all`) and DKIM on the `google` selector, all resolving. The DKIM key is
1024-bit, which is the size that fits Shopify's 255-character DNS field.

## Returns — PUBLISHED 31 July

The refund policy, terms of service and contact information are live and
correct. `[INSERT RETURN ADDRESS]` and all eight instances of
`abohn@onecountry.com` are gone. Old text backed up to `docs/policy-backup/`.

In force: **nothing is final sale**, **14 days from delivery**, customer pays
return shipping, no restocking fee, consumable/opened-cosmetic/intimates/custom
exclusions. Transit damage 48 hours; **defects keep 30 days on purpose** —
narrowing that converts refunds into chargebacks, which cost more and threaten
the payments account.

The vendor-variance problem has an answer that is not a number: **you are the
merchant of record.** Vendor terms decide how much you *recover*, not what you
*owe*. Internal triage, unpublished: under ~$25 refund and let them keep it,
because return shipping costs more than the item is worth.

**All five policies are live and clean.** Shipping policy published 31 July,
held back deliberately until the rate structure was settled. It describes
per-supplier rates calculated at checkout, separate parcels per brand, 5-10
business days (up to 15), and US only.

A final sweep for `onecountry` and `[INSERT` across all five found five more
placeholders in section 25 of the terms of service — trading name, address,
phone, registration number, VAT. Name and address are now filled; the other
three were removed rather than left as placeholders, since VAT does not apply to
a US retailer and the rest are not held. **The business address is now public**,
which is normal for a terms-of-service contact section.

**Markets confirmed US-only.** One market, "United States", enabled and primary,
region United States. Canada and International are not active markets, so there
is no international dead-end at checkout.

## Shipping — measured, and deliberately left as pass-through

**The customer pays the supplier's rate, unmarked-up, calculated at checkout.**
Shipping is net zero to us: we never lose money on it and never make any. That
is a decision, not an accident — see decisions.md.

**A flat $6.95 was attempted on 31 July and broke checkout.** Collective products
ship from SUPPLIER locations, so a delivery profile scoped to our own location
matches nothing: 6,994 variants returned no shipping rates at all and could not
have been bought. Reverted within minutes and verified recovered. The lesson is
in "Things that bit us".

**Every supplier is now measured** by the `shipping` agent, into
`vendor_shipping` metaobjects:

| shape | n | meaning |
|---|---|---|
| threshold | 25 | free above a cart value — median $84, 19 reachable |
| scaling | 9 | gets MORE expensive per item. Never upsell these |
| free | 9 | $0 at every quantity |
| flat | 5 | same rate however many items |

**Six of the 25 thresholds are unreachable** — August Uncommon Tea is free above
$56 and sells one $14 product. Reachability is measured, because no amount of
correct shipping data catches that; it is a fact about the catalogue.

**Per-product cost** lands in `ship.cost` (storefront-readable) with
`ship.checked_at`. Vendor shape predicts well but does not guarantee: Fuse Audio
ships six of seven products free and charges $12 on a heavy radio. A measured
non-zero cost MUTES the brand-level "free" claim.

Where it shows up:

- **PDP** — `aj-brand-shipping` block, placed and live
- **Cart + drawer** — per-brand progress bar and gap, then suggestions chosen to
  actually CLEAR the threshold
- **Yoink candidates** — anything shipping over 35% of its deal price is demoted
- **Bargain Bin** — same 35% rule excludes it entirely

**Products nothing will ship are now hidden automatically.** A product with no
shipping rate is as unbuyable as one with no stock and far more deceptive — in
stock, priced, entirely normal-looking, and a checkout that cannot complete.
The catalogue agent uses the same two-reading debounce as the sold-out sweep
(`no-ship-pending` then `no-ship-rate`), because a carrier service can fail
transiently and one bad answer should not take a product off the storefront. The
settled tag is also the permission slip to republish, so anything hidden by hand
is never resurrected — and a supplier fixing their rates gets their products
back with no intervention.

Products whose variants set `requiresShipping: false` are skipped. The first run
unpublished a gift card, which has no shipping rate precisely because it needs
none.

**Coverage after the one-time backfill:** 1,385 of 1,486 products carry their
own measured cost. **274 (20%) ship free** across 18 suppliers — nearly twice
what vendor-level sampling suggested, because vendor shape samples one
median-priced item and misses whole free catalogues. Median ship ratio is
**17%**, not the 41% an early 4% sample implied; that sample was biased by
design, since never-measured products are probed first.

**281 products (21%) ship for more than 35% of their price.** They are excluded
from Yoink candidates and the Bargain Bin automatically. They are NOT broken —
they sell fine, they just look bad — so they are left listed. Worst are
Sustainable Village's $1.57 Blumat adapter at $8.60 shipping (548%) and three
Sticker Fire designs at 334%.

**Not done, deliberately:** culling that 21%, and flat-vendor multipacks. Both
were judged not worth doing before there is any traffic.

## Returns — the Collective mechanics underneath

**This store is on Collective's current default**, not the legacy one. The legacy
"no action taken" default applies to retailers who joined before 10 December
2024; the shop was created 2026-07-29, so it cannot apply.

In force: supplier creates the return label, 2-day processing, 30-day window, no
label fee, no restocking fee, declined returns auto-cancel, refunds auto-refund.

Three things remain structural:

1. **You carry the customer-facing liability.** If a supplier does not refund an
   accepted return you must refund the customer and chase the supplier yourself.
2. **One returns policy for the whole store**, and supplier policies are not
   visible in the Collective app.
3. **Overriding shipping rates does not reduce what you owe the supplier.**

**So deep discounts on expensive items stay reckless.** Deal prices clamp to
cost, so at maximum discount the margin is near zero and any return cost is a
straight loss on a unit that never made money.

## Things that bit us, so they don't again

**From earlier sessions**

- `sections/*-group.json` is written by the theme editor, but repo edits DO
  apply. Retested 31 July: centring the logo and dropping the locale selectors
  from `header-group.json` went live on push. The earlier "repo edits are
  ignored" note was wrong. The real hazard is the other direction — the editor
  writes these files back, so `git pull` before touching them or the push
  conflicts.
- Shopify's client-credentials token expires in 24 hours.
- `metaobject.system.id` in Liquid is numeric, not a gid.
- Decimal metafields make Liquid division float. Round explicitly.
- API-created collections are published to nothing and 404 until published.
- Shopify price rules match ANY variant while the card shows the LOWEST.
- A truncated candidate pool destroys variety.

**From 30 July**

- **`tag:oos` also matches `oos-pending`.** Shopify's search tokenizes on
  hyphens. Read the `tags` array; never trust a `tag:` query to be exact.
- **`totalInventory` does not mean unsellable.** A variant with tracking off or
  policy CONTINUE sells at zero. Availability is a per-variant question.
- **Liquid's `image_tag` cannot take a hyphenated named argument.** Put the
  attribute on a wrapping element.
- **A guard that runs before the fallback it guards.** `discount <= 0` was
  rejected before the target-margin block that exists to derive a price when no
  discount was given — producing a day with no Yoink at all.
- **A forced bin rotation orphaned the week it replaced.** The live bin was
  excluded from the restore loop and the day-precision metaobject handle let the
  upsert overwrite the previous snapshot. Forty products left discounted with
  nothing owning the restore. Recovery worked only because compare-at still held
  the original prices — luck, not design.
- **Publishing to a Facebook Page needs a PAGE access token**, not the system
  user token Instagram accepts. The wrong one fails with "(#200) publish_actions
  ... deprecated", a permission removed in 2018 that has nothing to do with it.
- **An Instagram media container must finish processing before publish.** Too
  early fails with "Media ID is not available" (code 9007). Poll `status_code`
  until FINISHED — **and that is still not enough.** A 9007 killed a post four
  hours after the poll shipped: FINISHED and publishable are not the same
  instant. `media_publish` now retries on 9007 specifically. Untested, because
  `meta` has been paused since; expect to confirm it when the agent goes back
  on in August.
- **`utm_medium` must be `social`, not `organic_social`.** GA4 matches
  `^(social|social-network|social-media|sm)$` for Organic Social; anything more
  descriptive falls out of the channel grouping into Unassigned.
- **The theme id is 2, not 1.** `/cdn/shop/t/1/assets/...` returns a 404 page
  that is easy to mistake for stale content.
- **`categories.py` was never scheduled.** It was assumed to run on Actions and
  never did — category tags only updated when someone typed the command.
- **Constants in a `.server` module break the client build** if a component
  imports them. Split them out, as `schedule.ts` / `schedule.server.ts` does.
- **The app cannot read or create metaobject definitions.** Its scopes cover
  instances, not definitions. Create new types with the CLI; the app treats the
  denial as "already exists" and carries on.
- **Polaris `Text` does not accept `as="pre"`.** Use a span with
  `white-space: pre-wrap`.

**From 31 July**

- **A truncated query gives a confident wrong answer.** Twice in one day. A
  `variants(first: 3)` scan reported 36 published products with nothing buyable;
  the real number is zero, because a product whose first three variants are
  unavailable can have a buyable fourth. And the cart upsell's `limit: 12` made
  a whole filter tier unreachable. When a count feels surprising, check the page
  size before believing it.
- **A biased sample is worse than a small one.** The shipping sweep probes
  never-measured products first, so an early 4% sample put the median ship ratio
  at 41%. The true figure is 17%. The bias was designed in and I quoted the
  number anyway.
- **Vendor-level shape hides whole free catalogues.** Sampling one median-priced
  item per supplier found 179 free-shipping products; probing every product
  found 274 across 18 suppliers rather than 8.
- **Modal category by vendor is a trap.** Sweet Bamboo's most common category
  covers 23% of its products, prodigalpottery's 21%. Filling the gaps from the
  mode would have miscategorised the majority. `productType` was the honest
  signal.
- **Do not hand-write taxonomy ids.** `hg-12-3` is Outdoor Power Equipment, not
  Watering & Irrigation, and `hg-8-15` is not a category at all. Resolve by
  search, or reuse the id the vendor's already-categorised products carry.
- **Shopify rejects more than 25 metafields in one `metafieldsSet`.** A backfill
  batching 20 products x 2 fields silently discarded 250 results before anyone
  noticed `ok=0` in the log.
- **A cron endpoint is not a place for twenty minutes of work.** The shipping
  agent probes Collective's carrier service, which takes ~2.3s per call, and the
  first version budgeted 300 probes a run. It was killed by the request timeout
  every time, writing no heartbeat and no data — "Run now" simply appeared to
  hang. Budget long jobs in WALL-CLOCK TIME, not in call count: the cost of a
  call is not ours to control.
- **A time-boxed job needs a freshness rule or it never finishes.** Once
  budgeted, the run re-measured the same alphabetically-first suppliers forever.
  Skipping anything measured recently is what turns "as many as fit" into
  progress.
- **A swept deal that never records being finished restores forever.** Nothing
  cleared `price_snapshot`, so the lifecycle sweep re-applied a pre-deal price
  every fifteen minutes for the rest of time. Invisible until something else
  priced the same product — it was silently resetting two Bargain Bin members to
  full price within minutes of every rotation. Found by the invariants agent,
  which is exactly what it is for.
- **Collective products ship from SUPPLIER locations.** A delivery profile
  scoped to our own location matches none of them and returns no rates at all,
  which means the products cannot be bought. Check
  `productVariantsCount` on a profile and quote a rate before trusting it.
- **`deliveryProfileUpdate` takes `zonesToDelete` at the PROFILE level**, not
  nested in `locationGroupsToUpdate` where the shape suggests.
- **A filter cannot run inside a Liquid `if` condition.** `if x | handleize ==
  y` parses and then misbehaves; theme-check does not catch it. Assign first.
- **A candidate window can make a filter unreachable.** The cart upsell looked at
  the first 12 products of a vendor collection; the collection sorts by
  best-selling, the first thirteen were identically priced, and the item that
  actually cleared the shipping gap sat at fourteen. The tier worked perfectly
  and could never fire.
- **Sampling a live storefront gets you rate-limited.** A few hundred requests to
  `/cart/shipping_rates.json` earned a Cloudflare 1015 on our own shop. The
  Admin API's `draftOrderCalculate` returns the same numbers, needs
  `write_draft_orders`, and does not compete with customers.
- **Section groups CAN be edited from the repo.** The older note here was wrong;
  see the corrected entry above.

**From 30 July, later**

- **A cache key that omits the prompt freezes the output forever.** Enrichment
  hashed the product's source fields but not the prompt, so improving the
  prompt improved nothing — every already-enriched product matched its old hash
  and was skipped. Measured: 40 of 219 had the new field. The prompt is an input
  to the answer exactly like the description is. `PROMPT_VERSION` is in the hash
  now.
- **UTC is not a local time.** Deals were queued at `14:00Z` because that was
  9am Central the day it was typed. UTC does not observe daylight saving, so
  from 1 November every deal would have rolled over an hour early, silently and
  with nothing to catch it. Bare `--starts-at` values are store time now.
  **Entries already queued through 8 August still carry the old UTC times** —
  correct until November, not self-correcting.
- **The default delivery profile can contain zero products.** Rates configured
  there apply to nothing, and nothing warns you. Check
  `productVariantsCount` on the profile before believing a rate exists.
- **A published policy is a commitment whether or not anyone wrote it.**
  Shopify's boilerplate answered "who pays return shipping" in the merchant's
  name, months before anyone thought about it.
- **`deliveryProfileUpdate` takes `zonesToDelete` at the profile level**, not
  nested inside `locationGroupsToUpdate` where the shape suggests.
- **A metafield definition in an app-owned namespace rejects an explicit
  `access.admin`.** The error names a value the enum does not accept. Omit the
  field and let it default.
- **Backfill from stored data before bumping a version.** 623 metafields were
  written from values already sitting in the JSON blob; a `PROMPT_VERSION` bump
  would have re-run the model on 639 products to recover them.

## Next

- **Cull the shipping-absurd products** — Blessed Bayou Candles ($13.17 to ship
  a $5.62 candle), prodigalpottery, and the rest of the >40% band. Deferred, not
  rejected.
- **Flat-vendor multipacks.** Sticker Fire is $5.35 to ship one sticker or ten,
  so a 5-pack fixes 48 products that are unsellable individually. BLOCKED on an
  unanswered question: whether a Shopify bundle decomposes into a correct
  multi-unit Collective supplier order. Getting that wrong means unfulfillable
  orders. Also note a multipack goes unavailable when stock drops below the pack
  size, so it is MORE fragile than the single.
- **Guard inverted deal windows.** One `daily_deal` entry has `ends_at` earlier
  than `starts_at` and the scheduler accepted it.
- **"Also on sale" section.** Try the Admin API enum `IS_PRICE_REDUCED` before
  building a tag-based path — the admin UI rejects the rule, the API does not.
  The cross-sell also never excluded the live deal's product.
- **Turn `meta` on** when the teaser campaign ends.
- **Attribution gets real** from the first deal post carrying UTMs: Shopify
  Analytics → Sessions by UTM campaign.
- **Ads.** Everything so far is reversible; ad spend is the first thing that
  leaves and does not come back. Guardrails there need to differ in kind, not
  degree: a hard cap enforced in code, a spend ledger reconciled against Meta,
  campaign budgets set at Meta so the kill switch works when the app is down, and
  approval per campaign. Use `utm_medium=paid_social` so paid and organic sit
  side by side in one scheme.
