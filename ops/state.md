# Where things stand

Snapshot at the end of 1 August 2026. Written so tomorrow starts from facts
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
more than it did before, because it is where all nine agents live.

## The ten agents

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
| `digest` | 15 min | Emails agent health to `hello@` once each morning | Yes — **currently on** |
| `vendors` | Daily | Scores and ranks every supplier. Reads only | Yes — **currently on** |

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
`meta-app/make_teasers.py` and served from `theme/assets/teaser-*.png`.
**Regenerated on brand and restarted from q1 on 2 August** — see that section.
The original 30 July run was deleted by hand, because Instagram has no delete
endpoint.

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

The one left uncategorised is **Shipping Protection** — and the earlier note
here, calling it "the UpCart add-on", read as though we installed it. We did
not. It is vendor **Navigate Craft**, `productType` "UpCart - Shipping
Protection": a SUPPLIER's own protection SKU that synced into our catalogue
through Collective along with their real products. $12.50 against an $8.75
cost, three variants, zero inventory.

No category and no shipping rate, correctly on both counts — it is a service.
It is also **unpublished**, tagged `no-ship-rate` by the sweep, which is the
right outcome reached by the right route: a service has no shipping rate, so
the unshippable check caught it without anyone having to special-case it.

Worth knowing because it looks like a decision we made and is not one. **We do
not sell shipping protection** — see decisions.md.

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

1. **The calendar runs 1 to 11 August, and no further.** The `plan-aug2026fill`
   batch that filled through the 31st was cleared and replaced late on 1 August;
   see the incident section below. Eleven days is a real runway but it is not
   the month this line used to claim. **The invariants agent checks the runway**,
   so the warning will arrive on its own rather than waiting for someone to read
   this file.
2. **The Fidget Games** — 22 products unpublished and tagged `no-ship-rate`
   because Shopify offers no shipping rate for them, so checkout dead-ended.
   Needs raising with the supplier; nobody else can fix it.
3. **The 6 below-cost variants**, all Wags & Whiskers, worst $58.99 against a
   $62.15 cost. The catalogue sweep reports them every 30 minutes now; it will
   not fix them, because the price is the supplier's and dropping the line is a
   human call.
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
- ~~The shipping policy page is still unpublished.~~ **Published 31 July** — this
  line contradicted the Returns section two screens down and was simply stale.
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
- ~~No brand.~~ **Done as of 1 August.** Colours, both display faces and Archivo
  as the text face are all live, and Jake's logo is on the header. What remains
  is not a gap so much as a brief: Ohpixel is declared and barely used, and
  where else it belongs is a decision for Jake rather than something to invent.
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

## Shipping — measured, and marked up 15% since 1 August

~~The customer pays the supplier's rate, unmarked-up.~~ **Superseded.** Shipping
was net zero to us by decision until late on 1 August, when a 15%
percentage-of-rate fee went on the Collective carrier participant — see the
1 August, late section for the reasoning and the before/after rates. The rest of
this section describes how rates are MEASURED, which is unchanged: Collective
still calculates, and Shopify adds our margin to its answer.

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
label fee, no restocking fee, declined returns auto-cancel.

~~Automatic refunds are OFF as of 31 July.~~ **THIS WAS WRONG, AND IT SAT
UNDER EVERY RETURNS DECISION FOR THREE DAYS.** The Collective app was read on
2 August and Customer refunds was still set to **"Automatically refund
customer"**. Either it was never changed or it was changed back; the note above
recorded an intention as a fact and nothing checked it again.

It matters because the whole returns design assumed the opposite. With Collective
auto-refunding AND our own `refundCreate` switched on, every cash return would
have been **paid twice**. The only thing preventing that was our settlement
switch happening to be off — luck, not design.

**Set to "Collective takes no action" on 2 August**, which is Collective's own
recommendation when a returns app owns refunds. That makes this system the single
payer, and the trigger is worth knowing: the dialog reads *"After a supplier
refunds you"*, so Collective was never acting on close — it was passing the
supplier's refund along.

**Our settlement switch is ON as of 2 August.** It has to be: with Collective
taking no action, an unsettled return is a customer who never gets paid.

Three things remain structural:

1. **You carry the customer-facing liability.** If a supplier does not refund an
   accepted return you must refund the customer and chase the supplier yourself.
2. **One returns policy for the whole store**, and supplier policies are not
   visible in the Collective app.
3. **Overriding shipping rates does not reduce what you owe the supplier.**

**So deep discounts on expensive items stay reckless.** Deal prices clamp to
cost, so at maximum discount the margin is near zero and any return cost is a
straight loss on a unit that never made money.

## 31 July, later — margins, the calendar, and two silent holes

**The margin floor is net of fees now.** Both floors were measured against cost
alone, and the 2.9% + $0.30 sits outside the never-below-cost clamp, so "max
discount equals the supplier's margin" was wrong by the fee every time. Real
break-even is 43.6% on a $9 ornament, not the 50% the margin implies. Measured
across the catalogue, qualifying candidates fall 1,393 → 1,302; the 91 excluded
were sellable only at a loss. Survivors lose a median of 4 headline points.
`margin.ts` owns the fee model, `candidates.server.ts` uses it, and
`scripts/candidates.py` mirrors it so the CLI cannot answer a different question
about money.

**Two holes that had nothing looking for them:**

- **`loadCandidates` never excluded `oos` or `no-ship-rate`.** Unpublishing does
  not change `status`, so `query: "status:active"` still returns those products
  — 88 of them were in the deal pool, and a `no-ship-rate` Fidget Games product
  had been picked for 12 August. That is a deal priced, announced, counting
  down, posted to Instagram, with a checkout that dead-ends. The Bargain Bin had
  half the same hole: it checked `oos` and not `no-ship-rate`.
- **Nothing checked catalogue prices against cost.** The `never-below-cost`
  invariant only scans products WE priced, reasoning that a below-cost price
  "could come from our own actions" — false on dropship, where Collective sets
  both numbers. Six ACTIVE variants are underwater. The check now rides the
  catalogue sweep, which has already paged every product; it reports and never
  acts, because the fix is a supplier's price or a decision to drop the line.

**The deal queue is paged where it matters.** It went 11 → 35 entries in an
afternoon and every reader used a flat `first: 100`. The invariants agent pages
properly now and shouts at 200; the other seven readers went to 250. `lifecycle`
is among them, where truncation means a deal never activates or never restores.

**`queueDeal` refuses an inverted window.** One queued entry ends twenty hours
before it starts, so it can never run.

**Storefront, all live:**

- ~~The claimed bar hides below 30%~~ — **removed 1 August**, see below. The
  WCAG 1.4.11 failure in its track went with it.
- **Tomorrow's sneak peek**, below the add-to-cart on the homepage and the PDP,
  now its own block and carrying an AI-written hint. Category, a price band only
  when it is a LOW one, and drop time — never the product and never the
  discount — a Collective SKU is not exclusive, and a queued discount is intent
  until activation clamps it. Carries the email capture, which until now existed
  only in the footer with nothing offered for it.
- **A merch cart tier**, rendering nothing until `yoink-merch` has a product in
  it. Deliberately outside the shipping-threshold logic: we post merch
  ourselves, so it always adds a parcel and never clears a supplier's threshold.

**Metafields the storefront can now read:** `ship.vendor_shape`,
`ship.vendor_free_threshold`, `ship.vendor_reachable` projected onto every
product (3,819 backfilled), plus `ship.checked_at`. The `vendor_shipping`
metaobject is `PUBLIC_READ` but that is not enough on its own — reading a
metaobject over the Storefront API needs `unauthenticated_read_metaobjects`,
which lives on the public app and cannot be added without re-prompting every
merchant on it. Same wall the daily deal hit, same answer.

**Not a hole:** `SHOPIFY_WEBHOOK_SECRET` does not exist in this codebase.
Shopify signs app webhooks with the client secret and `SHOPIFY_API_SECRET` is
set; both webhook routes use `authenticate.webhook`, cron routes fail closed,
and the app-proxy vote route verifies its signature. The cron secret is
header-only now — the `?key=` form had no caller and only put the secret in
logs.

## 31 July, night — throttling, the digest, and a pile of new scopes

**Two agents throttled, and it was self-inflicted.** Catalogue and shipping both
returned `Throttled` within an hour of that afternoon's changes — a `unitCost`
field added to a query already pulling 100 products x 100 variants, and three
extra metafield writes per product on the shipping sweep. Fixed twice over: a
throttle-aware wrapper around the admin client (waits the amount Shopify states
in the response, capped at 10s and four tries), and the variant page size cut
from 100 to 25 with a top-up for the few products that have more. See
decisions.md for both, and for why the answer was not a supervising agent.

**A morning digest now emails `hello@` between 8 and 11am**, problems first,
branded HTML with a plain-text alternative. Sent through Google Workspace
because SPF authorises Google and nothing else — Resend or Postmark would fail
SPF from the first message. `hello@` is confirmed a real mailbox with its own
app password, which also closes the old "does hello@ actually receive mail?"
question. `SMTP_USER` / `SMTP_PASS` / `DIGEST_TO` are Fly secrets. Without them
it reports "not configured" rather than erroring, because an unconfigured
feature is not a broken one.

**Paused agents are never flagged.** The first real digest led with "Meta
posting needs a look" — an agent deliberately off until the teasers end, whose
last run before pausing errored. Left alone that heads the list every morning
for weeks, which is how a monitor teaches you to ignore it.

**The teaser agent was never broken.** It posts one a day, so 23 of every 24
hourly ticks correctly do nothing — and that branch returned without writing a
heartbeat, so the dashboard reported the last time it POSTED and called a
healthy agent 32 hours stale.

**A `returns/close` handler exists and does not pay.** It reads the closed
return, values it from its own line items, takes the WORST reason on a mixed
return, decides refund-vs-keep-it-and-credit, and writes a `return_decision`
metaobject keyed on the return id so a retried webhook updates one record
rather than creating a second. Registered as app version `theyoink-app-9`.

**72 scopes are now granted**, added in the Developer Dashboard.
`shopify.app.toml` was still declaring the original nine, so the next
`shopify app deploy` would have reverted them all — pulled and committed.

Two things that follow from that, and both are decisions rather than tasks:

1. ~~`write_orders` is granted, so the returns handler COULD refund. It still
   does not.~~ **Built on 2 August** — `refundCreate` works and is switched off.
   See "the returns handler can pay" below.
2. ~~There is still no store-credit scope.~~ **Wrong within hours of being
   written.** A later pull the same night brought the count to **77 scopes**,
   including `write_store_credit_account_transactions` and all five store-credit
   scopes. Both halves of the handler — `refundCreate` and
   `storeCreditAccountCredit` — are permitted.

   **The blocker is not scopes. It is that the store has zero orders.** Verified
   live on 1 August: `ordersCount` is 0, EXACT, and no return has ever existed,
   so `returns/close` has never fired. Execution written now could not be
   exercised against anything, and `refundCreate` is not a one-liner — it takes
   refund line items with quantities, a parent transaction to refund against,
   and its own decisions about shipping and tax. Those are the details that
   review passes and production fails.

   Unblocking it means a real order or a deliberately created test one, with a
   human present. **On a Collective store that is not a free action:** an order
   may be forwarded to the supplier as a real purchase, so "just make a test
   order" needs an answer about supplier fulfilment before anyone makes one.

**62 of the scopes are referenced nowhere in `app/`** — 72 at the time of
writing, 77 by the end of the night — and eleven carry real
blast radius: `write_discounts` and `write_price_rules` change what customers
pay, `write_checkouts` and `write_order_edits` alter live orders,
`read_customer_payment_methods` and `read_all_orders` are sensitive customer
data, `write_customer_data_erasure` is destructive. decisions.md already reasons
about exactly this for the Meta token: what a credential CAN do is the blast
radius when it leaks, independent of what the code chooses to do with it.

**Storefront, added tonight:** tomorrow's sneak peek below the add-to-cart on
both the homepage and the PDP, carrying the email capture that until now
existed only in the footer; and a merch cart tier that renders nothing until
`yoink-merch` has a product in it.

## 1 August — midnight rollover, the sold count, and three enrichment bugs

**The Yoink rolls over at midnight Central**, not 9am. The queue is rewritten:
31 windows from today, no gaps and no overlaps, with one 15-hour bridge on 1
August because a running deal must never be moved. Reasoning in decisions.md.

**Changing the constant alone would have shifted every deal back a day.**
`localDayStartUtc` derived the zone offset by comparing HOUR NUMBERS, which
breaks silently the moment the guess crosses a date boundary — midnight on 15
August returned 14 August. It measures the offset at the instant now, in two
passes so DST days converge; verified across 2026-11-01 and 2027-03-08.

**"Only N left" and the % claimed bar are gone**, replaced by "N yoinked today"
hidden below ten. The allocation was never enforced and the decision is that it
should not be — if a supplier has stock we sell it — which made the scarcity
line false at the moment it printed. The bar's WCAG problem disappeared with it
rather than needing a fix.

**Every product now carries an `enrich.teaser`**, a one-clause hint shown the
day before it drops. PUBLIC_READ, written under a rule it cannot break: evoke a
person or a moment, never the object. It renders as "Hint: …" under the factual
line in the sneak peek.

**The PDP is reordered.** Everything that argues for the sale is above the
button; everything else below. `aj-deal-urgency` was split, because it bundled
the countdown with the sneak peek and those argue opposite things. Two new
blocks: `aj-deal-price` (price, struck former price, saving pill — built on four
CSS custom properties so Jake's palette is a variable swap) and
`aj-deal-tomorrow`.

**A sold-out Yoink now says so and pivots.** "Gone. Today's Yoink sold out.",
and the sneak peek swaps its heading — "not your thing?" reads as a taunt to
someone who could not buy.

### Three enrichment bugs, all of which looked like working code

1. **`PROMPT_VERSION` was never in the hash.** decisions.md said it was fixed;
   the constant was imported into `enrichment.server.ts` and never referenced.
   Every prompt improvement since the port reached only products that happened
   to arrive afterwards. The symptom is a run that reports success and changes
   nothing.
2. **No wall-clock budget.** `MAX_PER_RUN` caps what a run ATTEMPTS, not what it
   SPENDS. Harmless while everything was skipped by hash; the moment the hash
   genuinely invalidated, a full run became 35 sequential model calls, blew the
   request timeout and died writing nothing. Same failure the shipping agent
   already paid for.
3. **Sequential model calls.** One ten-product call takes ~35s, so a run got
   through ten products. Now four in flight: **39 per run**. The Shopify writes
   stay serial deliberately — that is the shared bucket the sweeps compete for.

Also: queued deal products are enriched first, so the teaser reaches tomorrow's
Yoink within a run rather than around day forty; and the system prompt is
cached (~7.7k tokens read per run, four batches sharing one prefix).

**If a full-catalogue re-enrichment ever becomes routine, the answer is
Anthropic's Message Batches API** — async, 50% cheaper, 100k requests a batch.
Not needed for this backfill, which finishes in about a day at 39/run hourly.

### Shipping, later the same day

**A `Ships Free` smart collection**, handle `ships-free`, 279 products, sorted
price-ascending, published to all five channels. It is keyed on the `ship.cost`
metafield definition — which already carried `smartCollectionCondition` — so
Shopify keeps it current the moment the shipping agent writes a value. **No
agent work and no tag.** Verified: all 250 sampled members measure exactly zero.

**Cards carry a "Ships free" line next to the price** — `blocks/aj-card-ships-free.liquid`
on the theme's own cards (added to all five templates that render one), plus
inline markup in the Bargain Bin and Recent Yoinks, which draw their own tiles
and cannot take a block. Styles are one asset, `aj-ships-free.css`, so the three
sites cannot drift. Suppressed inside `ships-free`, where every card would have
it.

**The PDP shipping block now says what it costs.** A measured non-zero cost was
silent for scaling suppliers even though the number was sitting in `ship.cost`.
Also guarded: `checked_at` present with `cost` absent means Shopify offered no
rate at all, which would have had a free-shaped vendor's brand claim printed
over an unshippable product.

Live census, 1 August: **1,472 published, 279 ship free (19%), 1,168 paid, 25
unmeasured, 0 with no rate** — the 24 unshippable products this file recorded in
July are resolved. Free shipping is concentrated: Vogueen, Runic Dice, Navigate
Craft and AURA 8 HOME are 190 of the 279 between them, across 20 vendors total.

**Still manual:** nothing links to the collection. The app has no
`read_online_store_navigation` scope, so menus cannot be read or edited from
here — adding `Ships Free` to the main menu is an admin click.

**The sneak peek is a recessed panel**, not loose text — 0.045 tint, 0.18
hairline, its own padding, and an eyebrow reading "Tomorrow". Same on the
homepage and the PDP, both of which render `snippets/aj-deal-tomorrow.liquid`.

## 1 August, night — a stranded discount, and the one-Yoink rule

The August batch was cleared and rebuilt by hand. Seven new deals were queued
for 2 to 8 August. **One product was left discounted with nothing owning the
restore**, and it was found by reading the live queue rather than by anything in
the system noticing.

**Panama Hat Australian sold at $86.50 against a real price of $129.75** —
roughly a day, before it was restored. It carried no `yoink-of-the-day` tag, no
countdown and no badge: an ordinary-looking listing at a third off. That is the
worst shape this failure can take, because nothing about the storefront suggests
anything is wrong.

How it got there, in order:

1. Two entries for 1 August pointed at DIFFERENT products. `hasLiveDeal` guards
   against compounding a discount on the same product, so both passed it, and
   both were activated and repriced. A day has one Yoink, so only one could show.
2. The clear then ran. `undoBatch` correctly refuses to delete an entry carrying
   a `price_snapshot` — that snapshot is the only record of the real price — but
   it reported this as `keptActivated: 1`, a number with no product in it.
3. The survivor's window had been moved to 11 August, so the sweep that would
   have restored it was not due until the 12th.

**Compare-at would not have saved it.** The bin-rotation orphan in July was
recovered because compare-at still held the original prices; state.md called that
luck at the time, and this is the case that proves it. Here compare-at held the
$173.00 MSRP, not the $129.75 we were charging. The `price_snapshot` field was
the only surviving copy.

Both holes are fixed and deployed:

- **One Yoink at a time.** `liveDealNow` asks whether ANY deal is running, not
  just one on the same product, and activation refuses while one is. Checked
  before the product is fetched so a blocked deal costs nothing. It reports to
  `errors`, not `skipped`, because overlapping windows are a misconfiguration and
  the light should stay red until the schedule is fixed. **The trade is real:** a
  stranded activated entry now blocks activation for the length of its window —
  the Yoink goes dark for a day and says so loudly, naming the blocking handle —
  rather than letting a second product be silently discounted.
- **`undoBatch` names what it kept**, with product, deal price and window,
  instead of counting it.

**Restoring it was done by hand, not with `deal.py end`.** That command winds
`ends_at` back to now, which on an entry whose window has not opened yet writes
an INVERTED window and leaves the snapshot in place. The advice to use it has
been removed from the dashboard message that used to suggest it.

**9 and 10 August were filled** — Gleamin's Vitamin C Clay Mask at 35% and White
Water Life's Hampton Pullover at 38%, the latter hero score 4 and shipping free.
Clearing the snapshot on the Panama Hat entry also turned it back into an
ordinary queued deal, so 11 August recovered on its own.

**`candidates.py` still has the hole this file records as fixed.** The `oos` and
`no-ship-rate` exclusions landed in `candidates.server.ts` and never reached the
Python mirror, whose query is still a bare `status:active`. The CLI can hand you
an unbuyable product. Both picks above were verified by hand instead. The mirror
is meant to make the CLI and the app answer the same question about money; on
this question they do not.

### Corrections to earlier entries

- **Judge.me IS wired now.** This file said no review UI was wired; that was
  true until 1 August, when the review-widget block was added in the theme
  editor. It renders on the PDP and on collection cards. `number_of_reviews` is
  0 — the gap is having no orders, not missing UI.
- **The scheduler's stagger only ever applied to the first run.** See below.

## 1 August, late — returns proven, Yoink Sweep retired, shipping earns

### The returns handler ran for the first time

**`returns/close` had never fired in this store's life**, so nothing had ever
tested it. It turned out to be broken in a way no amount of review would have
caught, because the failure was in a permission rather than in logic.

**The app held no returns scope at all.** Its first action is a `return(id:)`
read, which answered `ACCESS_DENIED — requires read_returns`, verified against
the live store with the app's own token. Worse than a plain bug: every failure
returned 500 on the reasoning that a read failure is usually transient, and
Shopify retries a non-2xx for 48 hours and then DISABLES the subscription. A
missing scope is not transient, so the handler would have taken itself down for
every future return, days later, with nobody watching. Permanent failures now
answer 200 and log loudly instead.

**All scopes are now granted — 183 of them**, deliberately, so nothing is
blocked waiting on a permissions round-trip. The standing rule that comes with
that breadth: **ask before building anything that uses a scope the code does not
already use, and before using one by hand.** Availability is not permission. The
guardrail moved off the token and onto the asking.

**A test harness exists and cost nothing.** `TEST — Returns Harness (do not
sell)`, vendor `Yoink Internal`, **DRAFT status on purpose** — every agent
queries `status:active`, so a draft product cannot be picked as a Yoink or pulled
into the bin. No supplier behind it, so no Collective order can result. Three
variants priced to land in three different branches: $18 under the keep-it line,
$40 ordinary, $100 above the approval line.

Order **#1001** ($40, tagged `internal-test`) and return **#1001-R1** exercised
the path end to end. The record written:

```
rd-57347047526   action=refund_cash   refund_value=40.0   reason=UNWANTED
                 we_pay_return_shipping=false   credit_amount=44.0   status=pending
```

Correct on every field — valued from its own line items rather than the order
total, handle derived from the return id so a retry updates one record. **Three
branches remain untested**: $18 fault, $18 non-fault, and $100. Worth doing
before any money-moving code goes near this.

~~Still nothing pays.~~ **Cash refunds pay as of 2 August**, off by default —
the details that "review passes and production fails" turned out to be real, and
the answer was to let Shopify compute them rather than to write them carefully.
Store credit is still unbuilt. See the 2 August section below.

### Yoink Sweep is retired

**It had no codebase.** It was a second Shopify app whose client id and secret
sat in this repo's Actions secrets, driving two workflows —
`sweep-expired-deals.yml` and `sync-catalog.yml`. Everything they ran already
lives in the app: `deal.py activate`/`sweep` became the lifecycle agent,
`bands.py` and `vendors.py` became the catalogue agent. Both had been disabled
since 30 July.

Deleted rather than left disabled. A dormant second scheduler that activates and
sweeps deals is not a harmless fallback — re-enabled by accident it fights the
lifecycle agent over the same metaobjects and the same prices, and this project
has already paid once for two systems believing they owned a restore.

The reason it existed separately is also gone: it held
`write_metaobject_definitions`, which the app lacked. The app now has it.
**`unauthenticated_read_metaobjects` is granted too**, which this file twice
records as a hard wall keeping the Storefront API blind to the daily deal. That
wall is gone and worth revisiting.

The Python scripts do NOT depend on it — `shopify_auth.py` falls back to the
Shopify CLI when the env vars are absent, which is the path they take locally.

**`candidates.py` had the hole this file recorded as fixed.** The `oos` and
`no-ship-rate` exclusions landed in `candidates.server.ts` and never reached the
mirror, whose query was a bare `status:active` — and unpublishing does not change
status, so the CLI could and did offer unbuyable products. 1,607 → 1,564.

### Shipping earns 15% now

**The customer paid the supplier's rate at exactly cost and we kept nothing**,
while carrying the conversion drag of a median $6.40 added to a $37.99 item.

Shopify's `DeliveryParticipant` carries `fixedFee` and `percentageOfRateFee`,
applied on top of whatever the carrier returns. On the Collective participant
both were unset. **`percentageOfRateFee` is now 15.**

**A PERCENTAGE, NOT A FIXED FEE, AND THAT IS THE WHOLE DESIGN.** 279 products are
marketed as shipping free — the `ships-free` collection, a line on cards in five
templates, a PDP block — all keyed on the measured cost being zero. A flat $1.50
would leave every one of them claiming free shipping while checkout charged for
it: the same class of failure as the "Only N left" counter nothing enforced. 15%
of $0 is $0, so the claim stays true with nothing to keep in sync.

Verified by quoting live rates before and after:

| | before | after |
|---|---|---|
| Hampton Pullover, free option | $0.00 | **$0.00** |
| Hampton Pullover, Standard | $10.00 | $11.50 |
| Vitamin C Clay Mask | $4.90 | $5.64 |
| Panama Hat Quickstep, Ground | $17.78 | $20.45 |

Every product still returns rates. **This is not the July flat-rate attempt**,
which replaced the rate SOURCE with a profile scoped to our own location, matched
no Collective product and returned no rates at all. Here Collective still
calculates; Shopify adds to the answer.

**`ship.cost` now means what the CUSTOMER pays, not what the supplier charges.**
The shipping agent measures through `draftOrderCalculate`, the same path, so its
next run records marked-up figures. Correct for the PDP line and the cart
threshold, which should show the real price — but it shifts the 35%-of-price
exclusion slightly, so the deal pool shrinks a little. Free stays zero.

**An order that clears a vendor's free-shipping threshold earns no markup.** That
is the right trade and not a flaw: clearing a threshold adds an item worth ~$10.22
in contribution against the ~$0.96 of shipping margin given up. Roughly ten to
one. The markup is self-limiting exactly where you are already making more.

### What the numbers say about the model

Measured across 1,516 products carrying both a price and a cost, net of fees:
**full-price contribution $10.22** (30% of a $37.99 median), **Bargain Bin at 25%
off $6.53** with only 45% of the catalogue eligible, **Yoink $4.02**.

**The acquisition offer is the lowest-margin thing we sell.** Max supportable CAC
at 3:1 is **$6.69** on realistic assumptions and **$20.44** at the absolute
ceiling — no deals at all, 50% attach, 4 lifetime orders. Cold paid acquisition
runs $25-60. The gap is 3-5x, and no repeat rate a new brand can assume closes it.

This does not say the model fails. It says **paid cannot buy the first cohort.**
Build the list organically, then paid becomes retargeting off that list at
$12-18, which the model does support. And **AOV is the strongest lever**: at $35
CAC and 4 orders you need $82.71 AOV against $37.99 today — which is why the
same-vendor threshold upsell already in the cart is the highest-leverage thing
built so far.

Fixed costs are not the constraint. Roughly **30 full-price orders a month covers
the entire operation.**

## 1 August, night — the brand lands, and the crash was never a crash

### Jake's palette is live

```
#7a3fa0  purple   act      links, primary buttons
#ffe000  yellow   grab     the saving, the badges
#30aac6  teal     surface
#5cd8f8  cyan     surface
#282828  ink      read
```

**Ink for reading, purple for acting, yellow for grabbing.** Text is `#282828`
rather than pure black — it is Jake's ink and the ground his yellow and cyan were
chosen against.

Measured, not eyeballed:

| pairing | ratio | |
|---|---|---|
| ink on white | 14.74:1 | body |
| white on purple | 6.89:1 | primary buttons |
| ink on yellow | **11.17:1** | the saving, the badges |
| yellow on purple | 5.22:1 | safe, and unusual luck |
| **yellow on white** | **1.32:1** | never — effectively invisible |
| **white on teal** | **2.73:1** | never — looks fine on a good monitor |

Yellow only ever appears as a BACKGROUND carrying ink. Teal and cyan carry ink,
never white. Purple is the only brand colour safe as type on white.

**The `foreground` slot is overloaded and that shapes everything.** In this theme
it drives body text AND the primary button background AND the sale badge
background from one token, so it cannot simply be set to purple without turning
every paragraph purple. It stays ink; buttons and badges are overridden
individually in `settings_data.json`.

**Sold-out is deliberately not the brand yellow.** Its schema default points at
`color2`, which is now yellow, so leaving it alone would have painted "gone" in
the colour that means "grab this". A colour that means both means neither.

`assets/aj-brand.css` holds the variables and is loaded from the layout head,
because three separate files read `--aj-price-*` through their own
`stylesheet_tag` — defining them anywhere narrower leaves two of the three on
neutral fallbacks.

**Setting the palette changed nothing visible at first.** This storefront does
not render the theme's badge component: `color-custom-badge-sale` appears four
times in the page source, all inside `<style>`, and ZERO times in the real DOM.
The badges people see are `aj-deal__badge` ("Save 44%") and `aj-bin__badge`
("25% off"), drawn by the Yoink and Bargain Bin sections, which build their own
tiles and take no theme block. Both were hardcoded to `--color-foreground` and
never looked at the brand at all. They read the brand variables now.

**Fonts are scaffolded and switched off.** Flashy and Ohpixel are not in
Shopify's `font_picker` library, which only serves Shopify's own set, so they
need real `.woff2` files in `assets/` plus **a licence covering web embedding** —
a separate tier from desktop for most display and pixel faces, and the thing to
confirm before building on them. `--aj-price-font` stays unset so every consumer
falls back to the theme heading font rather than silently landing on a face
nobody chose. Type is Inter throughout until then.

The logo path is independent: artwork drops into the `logo` setting that already
holds `Logo-Test-2.png`, with no font licence involved.

### The crash was three full catalogue scans, and it is fixed

**Nothing ever crashed.** No OOM — a full scan is 11-16 MB against 317 MB free.
No throttling — 1999/2000 available. No restarts. `/app/new` and `/app/plan` were
simply taking **15.4s, measured**, and 15-45 seconds of blank screen inside an
embedded admin frame is indistinguishable from a dead app.

Where it went: **7.6s** paging the catalogue, **~7.7s** topping up the 64 of
1,655 products whose variant list exceeds `VARIANT_PAGE` — one sequential round
trip each. Half the page load was latency paid in series.

Then it compounded. Remix re-runs a loader after each of its actions, so
clearing a batch and scheduling seven paid the full scan **three times**, on a
shared single vCPU also running `catalog` (54s), `enrich` (84s) and `shipping`
(37s).

Two fixes: the top-ups run five at a time, and the raw scan is cached for 90s.
**Measured after: 15,356ms → 8,763ms**, and near-instant on a reload inside the
window. What is cached is the FETCH, not the ranking — ranking is CPU work over
an array, so caching raw lets every filter combination and both pages share one
copy. An empty scan is never cached, so a transient failure cannot show "nothing
qualifies" for ninety seconds.

**A skipped product no longer fails the enrich run.** The model returned nine of
ten and the run reported `FAILED 500` after enriching forty products. The
handling was already right — the product keeps its hash and comes back — but the
note went into `result.errors`, and `cron.enrich` fails on any error. Counted as
`modelSkipped` now, escalating to a real error only above 20% of what was
attempted, which would mean the prompt or the id matching is broken rather than
the model being lazy.

## 1 August, small hours — the type system, and a lot of getting it wrong

The palette section above records the colours. This is the type and the layout,
and the honest version is that most of it took three or four passes because the
mistakes only became visible on screen.

### Three faces, three jobs

Jake supplied **Flashy** (logo main) and **Ohpixel** (sub) as `.woff`. Both are
live, converted to woff2 with woff fallback, and verified before being switched
on: Flashy carries all ten digits plus `$ . , % -` across 241 glyphs, Ohpixel
carries an embedded licence string reading "Personal & Commercial use".

**Neither is a text face, so a third was always needed.** **Archivo** replaced
Inter, chosen because it is the only candidate that sits WITH a retro display
face rather than politely ignoring it, and it stays readable at the 14px where
product copy lives. It is in Shopify's library, so it cost a setting rather than
a licence.

| face | job | where |
|---|---|---|
| Flashy | display | section headings we write, drawer and popup titles |
| Ohpixel | accent | eyebrows, badges, the countdown, footer column headings |
| Archivo | text | everything else — roughly 90% of the words |

**The price is NOT in the display face**, and that was learned the hard way.
Flashy at 1.75rem rendered thin and cramped and was genuinely hard to read as
numbers. It is Archivo at 3rem/800 — money should look like money, and borrow no
personality it does not need.

**Flashy is on headings WE write, never on product titles.** It was applied to
`h1-h4` and the first live deal rendered as three lines of `DUNGEONS & DRAGONS:
THE ULTIMATE POP-UP BOOK (REINHART POP-UP STUDIO): (D&D BOOKS) (REINHART
STUDIOS)`. Selectors are listed one by one now, for a verified reason — see the
`<h3 class="h4">` entry below.

**The countdown reads `02:27:14`.** It said "2 h 27 m 14 s", which is number,
word, number, word — the shape of a sentence, fighting the LED idiom the pixel
face borrows. It sits in an ink panel with yellow digits at 11.17:1. Dropping
the h/m/s letters costs nothing in accessibility: every unit group is
`aria-hidden` and the component keeps a separate `visually-hidden role="status"`
region announcing the real remaining time.

### The Yoink of the Day section was a generic product hero

It was a 50/50 centred grid — the same shape as any product block, for the
section that is supposed to BE the concept. Equal columns gave the photograph
and the offer identical weight; `align-items: center` left the offer floating in
mid-air beside a tall image, anchored to nothing.

Now **1.15fr / 0.85fr, both columns starting at the top**, so eyebrow → title →
price → clock → button reads as one descending stack in the order someone
actually decides in. The offer sits on a panel tinted 12% from the brand cyan,
mixed into whatever ground the section's colour scheme uses rather than assuming
white.

### Recent Yoinks was dead rather than missed

The section's own comment says its job is to make a card land as a LOSS —
and it was dimmed **three times over**: `grayscale(1)`, `opacity: 0.62`, AND a
42% ink veil. Any one reads as past; all three read as a graveyard, which is the
opposite of the intended feeling. There is no regret without desire.

The veil stays, because it is what guarantees the white "81% off" is legible
over an arbitrary product photo. The other two went. **Half desaturation** keeps
today's live deal unmistakably the thing to act on while leaving the product
recognisable as something you wanted — and it matters that the resting state
works alone, because the hover restore never fires on a phone.

**Every card was also printing its screen-reader labels** — "$136.98 discounted
price $249.05 regular price". Clipped now. But clipping them removed the meaning
for sighted readers too: two bare numbers where the struck one is LOWER reads as
a price rise, since everywhere else a struck price is the higher one. The word
**"now"** before the current price carries it in three characters.

### Still not right

- **The day labels.** A recent screenshot showed Saturday / Friday / Thursday /
  Tuesday — Wednesday missing, and "Saturday's Yoink" is ambiguous against a live
  Saturday deal. A gap makes the sequence look broken, which undercuts the
  section's PROOF job.
- **81% off on the sheet set** is measured against a $279 MSRP. Not false, but
  the same trap this file already records for the Bargain Bin, and the kind of
  number that invites doubt on a first visit.
- **Product titles are bad data.** "(Reinhart Pop-Up Studio): (D&D Books)
  (Reinhart Studios)" is vendor and category jammed into the title by
  Collective's feed. No typeface fixes that.
- **The logo is Jake's real artwork now**, but Ohpixel is declared and barely
  used. Section eyebrows and the countdown are the natural homes; anything more
  needs direction rather than invention.

## 2 August — the teaser campaign, rebranded and restarted

### The cards are on brand

`meta-app/make_teasers.py` generated them monochrome, and its own docstring said
why: there was no palette and no typeface, and inventing one for a teaser
campaign would have quietly let it become the brand by default. Both now exist,
so the flat-colour-field decision stops being an avoidance and becomes a choice.

**Statements in Flashy, signature in Ohpixel.** Every card names an explicit
`(ground, ink)` pair rather than a light/dark flag, none below 5.2:1 — yellow on
purple at 5.22:1 is the logo's own relationship. White on teal is absent on
purpose. No two adjacent cards share a ground, which is what the old alternating
black-and-white was doing and the one thing worth keeping.

**The statements are NOT in the pixel face, and that was tested rather than
argued.** Instagram's profile grid renders a 1080 card at roughly 120px, and
Ohpixel's strokes are thin enough that it visibly fades there while Flashy still
punches. Rendered both side by side with a grid-scale strip underneath to decide.

**Every card signs itself `theyoink.com`** — small, in the pixel face, which is
the short-label shape it is drawn for and its first real job. These get
screenshotted and reposted without a caption, and a card that does not say where
it came from is doing no work when that happens.

Fonts are bundled as TTF beside the generator because Pillow cannot read the
WOFF the theme serves.

### The campaign restarted from q1

All nine `social_post` records were reset to `queued` with `posted_at`,
`instagram_id` and `facebook_id` cleared. **q1 and q2 posted on 2 August**; q3-q9
run one a day from 3 August and finish around **9 August**. The agent's
twenty-four hour gate handles the rest — `?force=1` is what posts a second in
one day.

**`meta` stays paused until then.** Turning it on early puts a product ad in the
middle of a teaser sequence, which is the reason it was paused in the first
place.

### Deleting the old posts was most of the work

**Instagram has no delete endpoint.** Confirmed against Meta's Content Publishing
docs: containers, uploads and publish, and nothing that removes media. Published
media also cannot have its image replaced — a caption can be edited, the picture
cannot. **So a rebrand mid-campaign means deleting by hand, in the app, one post
at a time.** There is no automating around it.

**Facebook deletes only what the same app created.** Five of six old Page posts
went via the Graph API; the sixth refused with `(#200) This post wasn't created
by the application`. That one is a duplicate "Now you know the word." from
31 July 19:04, alongside the app's own copy from 30 July — **so something other
than this app posted to the Page.** Worth knowing what else holds credentials
there, given the Meta token carries `ads_management`.

Deriving a Page token for any of this is `GET /{pageId}?fields=access_token` with
the system user token; the system token itself cannot read or write Page posts.

### The mistake worth recording

**q1 was posted on the strength of "deleted them" without checking**, and the old
q1 was still live, so the account briefly carried two "What is the Yoink?" posts
and they had to be cleared by hand. The account state was one Graph API call away
and the credentials were already to hand. **Verify the destination, not the
report about the destination** — the same rule this file already keeps for the
Shopify catalogue, applied one system over.

## 2 August — the returns handler can pay

**`refundCreate` is built, proven, and switched OFF.** That is the resting state
and it is deliberate.

### How it is guarded

**Shopify computes the refund; we do not.** `order.suggestedRefund(refundLineItems)`
returns the amount AND the transactions to refund against, each already carrying
the correct gateway and parent transaction. Hand-building those is exactly where
this goes wrong in ways that pass review — the parent is the original sale, the
gateway has to match it, and tax and shipping are not ours to guess at.

**But we check its answer.** If Shopify's figure and the decision's own
`refund_value` differ by more than a cent, nothing is paid. Both are derived from
the same line items by different code, so a divergence means one is wrong and
neither is trustworthy enough to spend on.

**The switch has NO environment fallback.** Every other agent falls back to an
env var when no metaobject has been set. This one must not: an env var is set
once, somewhere nobody looks, by someone who has since forgotten. Fine for
pausing a catalogue sweep, wrong for authorising refunds. **Absent means off,
and unreadable means off.** The handle is `agent-returns-pay`.

**Only cash actions pay.** `needs_approval` exists to stop the arithmetic
spending on its own and must never pay itself. `keep_it_and_credit` owes store
credit, which is `storeCreditAccountCredit` — a different call, and cheaper than
cash by design.

**Idempotency is the `status` field.** `pending` is the only payable state, and
the record is marked `paid` only AFTER the money moved. The other order would
leave a record claiming paid when nothing was, which is the one lie this system
cannot afford.

**A payment failure does not fail the webhook.** The decision is written first,
so a failure loses the money movement and not the reasoning — the record still
says pending and can be paid later. Retrying the whole handler would re-run a
path that may have half-succeeded.

### NEVER RESTOCK, and it is not a simplification

The first live attempt failed with `refundCreate: You need to set a location to
restock items`, and the fix is a fact about this business.

**Every sellable product here is Collective dropship** — shipped from a supplier
location and returned to one. Nothing ever arrives at a location we own, so
restocking would invent inventory that is not in any building we have, and the
only `locationId` we could name would be the wrong one. On a keep-it decision the
customer still physically has the item, which reaches the same answer by a
shorter route.

### Proven both ways

| switch | result |
|---|---|
| OFF | decision recorded `pending`, **zero** refunds on the order |
| ON | decision `paid`, **one $40 refund**, order `REFUNDED` |

Run against throwaway orders on the draft-status test product, completed with
`paymentPending: false` so the payment is a manual record rather than a card
charge and the refund moves no real money. All test orders deleted afterwards;
`ordersCount` is back to 0.

**Five `return_decision` records are kept on purpose.** They are the only worked
examples of what correct output looks like, including one `paid` and one
`needs_approval` at $118 from a mixed-reason return.

### Store credit works too

`keep_it_and_credit` settles now — `storeCreditAccountCredit` against the order's
customer. Tested live: an $18 UNWANTED return produced **$19.80 of credit**,
balance verified, record marked `credited` rather than `paid` so a reader can
tell at a glance whether someone got money or spending power.

**CREDIT IS A DIFFERENT SETTLEMENT, NOT A CHEAPER REFUND.** Nothing goes back to
a supplier on a keep-it decision, so there is no recovery to wait for and no
refund to create. The customer already has the goods; what they get is spending
power.

**NO EXPIRY, DELIBERATELY.** The 110% multiplier is worth more to them than cash
AND costs us less, because credit is costed at COGS — roughly $9 of real cost for
$19.80 of credit on a 50%-margin item. That margin is the whole reason the action
exists. Breakage is not, and an expiry date would turn a generous-looking offer
into a trick.

**Both settlements share one switch.** Cash and credit both move value, so
neither can be turned on alone — nobody gets to enable "only the cheap one" and
forget which is which. It refuses when there is no customer on the order, because
credit needs somewhere to go.

### Does keep-it-and-credit fit Collective?

**Yes, because it is downstream of Collective entirely.** Collective governs what
happens when goods go BACK to a supplier — label, 2-day processing, 30-day
window. On a keep-it decision nothing goes back, so none of that engages. What
the customer receives is ours to decide.

The consequence is economic, not contractual: **no return means no recovery**, so
we eat the full wholesale cost. That is the deliberate trade — on an $18 item
return postage plus handling costs more than the item recovers, and recovery from
the supplier was never guaranteed.

Note we are STRICTER than Collective on the window: our policy is 14 days for a
change of mind against Collective's 30. Normal, but it means a day-20 request is
one Collective would accept and our policy would not.

### Returns start by EMAIL, not self-serve — and the reason is sequencing

Decided 2 August. `hello@theyoink.com` is the route; Shopify's self-serve returns
stay off.

**Self-serve would generate return labels on exactly the items the policy says
should not come back.** A customer self-serving an $18 return creates the return,
Collective generates a label, the item ships — and only when the return CLOSES
does the keep-it logic run and conclude they should have kept it. Postage paid on
something we had decided not to recover, and a confused customer.

The decision engine fires at close. Self-serve commits before then.

**Switch self-serve on when keep-it can be decided at return CREATION rather than
close.** That is real work and worth doing when volume justifies it. Until then
the manual step is also the only chance to check the $25 line and the 110%
multiplier against real human reactions before they are automated.

## 2 August — returns became a system a customer can actually use

### A form, not self-serve, and not the mailbox

`theyoink.com/pages/start-a-return`, posting through the signed app proxy at
`/apps/yoink/return`.

**Self-serve was rejected for sequencing, not caution.** It creates a Shopify
return the moment a customer asks, Collective generates a label, the item ships —
and only when that return CLOSES does the keep-it logic decide they should have
kept it. Postage spent on something already decided not worth recovering. A form
does not create a return; it captures a request, so **the decision happens first
and only items worth recovering ever get a label.** Self-serve returns were
switched off in Shopify on 2 August.

**The mailbox was rejected because nothing reads it.** Free text is poor input
for something that moves money.

**THE EMAIL IS THE PASSWORD.** Order numbers are sequential and guessable, so
nothing is returned unless the email matches — and every failure answers with
identical wording whether the order is missing or the email is wrong, because a
different message for each turns this into a tool for discovering who bought what.

### Keep-it is an OFFER, and cash means the item comes back

Both corrections came from Alex reading the copy, and both were mine.

**Imposing credit is a refund refused**, however generous the number. The 110%
multiplier exists to make credit ATTRACTIVE and an incentive needs something to
choose between. So under $25 the customer picks:

- **Keep it, take $19.80 credit** — nothing to mail back, more than they paid
- **Send it back for $18.00** — a real return and a real label

**Refunding in full while they keep the goods is not a policy, it is a hole.**
The first version offered cash without a return, which is free product for anyone
who notices. Cash now always creates a return.

The offer copy was also written from OUR side — "it costs more to mail than it's
worth" tells a customer their item is too cheap to bother with. From theirs it is:
keep the thing, and have more than you paid to spend again.

### The approval line is $24.99, a cent below the keep-it line

Was $75, which meant the form created a real return and dispatched a real label
on a $40 request with nobody looking. **Now the only thing acting unattended is
the keep-it case**, which costs postage nothing and is the answer a human would
have given anyway.

**A cent below `keepItBelow`, not equal to it.** The keep-it test is `value <
keepItBelow` and the approval test is `value > approvalAbove`; setting both to 25
leaves exactly $25.00 matching neither and falling through to an unattended
label. One value is precisely the hole nobody finds until it happens.

### How a Collective return actually works

Read from the Collective app on 2 August rather than inferred:

- **Supplier creates the return label within 2 days.** 30-day window, no label
  fee, no restocking fee. Cancelations manually reviewed.
- `returnCreate` makes a reverse fulfillment order but **no label** — the
  supplier approves and uploads one, Collective syncs it, the customer is emailed.
  A two-day SLA is why watching for sixty seconds proves nothing.
- **`reverse_deliveries/attach_deliverable` is now subscribed** (app version
  `theyoink-app-14`) and writes `label_sent` onto the matching request. Without it
  we started returns and had no idea whether a label ever reached anyone.

### Everything else that moved

- **The refund policy points at the form**, not `/account`. The old text sent
  customers to the exact self-serve flow this design avoids.
- **The footer said "Orders & returns" and linked to `/account`** — the same trap.
  Now "Start a return" first, with "Your account" kept separately. **Navigation IS
  editable from here now**; the note saying it needed an admin click is stale.
- **Customers get an email** for every outcome, through Google Workspace like the
  digest, each carrying its own next step — credit shows at checkout, refunds take
  business days, a label arrives separately, an approval means do not mail
  anything yet. Sending can never fail the request.
- **The digest shows form requests as well as closed returns**, marked with which
  is which, because a keep-it request never becomes a Shopify return and was
  invisible.
- **The copy is American.** color, defective, business days, ship it back, right
  away. Markets is US-only and the copy was not.

## 2 August, evening — navigation got a second level, and the 404 earns its keep

**Eight of twenty-one category collections were linked.** The other thirteen —
Sporting Goods (53), Furniture (51), Office Supplies (43), Books (41), Vehicles
& Parts (30), Baby & Toddler (26) and a tail below ten — held roughly 272
products that nothing on the site pointed at. The catalogue agent had been
creating them correctly since 31 July and then nobody surfaced them. Creating a
collection and linking a collection were never the same job, and only one of
them had an owner.

**Depth was the other half.** Keeping only the top taxonomy segment is still
right for most of the catalogue, but it put 622 products in one Apparel bucket,
369 in Home & Garden, 215 in Toys & Games. That is a wall, not navigation — and
95% of products already carried the second level needed to split it.

Now: fourteen top-level entries, thirteen sub-collections, 1,319 products
tagged and all 1,319 landed (counts reconciled against the collections, not
assumed from the mutation count).

**The agent does this itself now, on thresholds rather than a list.** A
hardcoded "split these four" would have been correct the day it shipped and
wrong the first time a supplier's range grew. `catalog.server.ts` counts
children from the catalogue it already loads each run: a top-level over
`SUB_TOP_MIN` (120) gets split, each child over `SUB_MIN` (15) gets its own
collection, and a child that shrinks back below the line has its tag removed. A
child named after its parent is skipped, because Shopify's taxonomy repeats
itself — "Animals & Pet Supplies > Pet Supplies", "Media > Books" — and
splitting those asks you to click Pet Supplies to reach Pet Supplies.

**Checked the theme renders three levels BEFORE tagging anything.**
`mega-menu-list.liquid` does recurse `parent_link.links` → `link.links` →
`childLink`. Had it not, this would have filed 1,319 products into collections
nobody could reach — which is precisely the bug being fixed, committed twice.

**Shop by price is a dropdown now**, with Ships Free in it. The band collections
are handled `under-10`, `10-to-20`, `20-to-30`, `30-to-50`, `50-and-up` — NOT
`band-*`, which is the tag prefix, not the handle. Rendered as tiles: a price
menu of six uppercase words makes you read six lines to compare six numbers,
when the number is the whole choice. Scoped by collection href because the theme
gives every dropdown the same class, and flattened with `display: contents`
because `mega-menu-list.liquid` varies how many links share a column. Ships Free
is purple rather than yellow because it is a different axis, not a price band.

**The header teal was never a brand colour.** `background_color_top` was
`#43afca` and `text_color_top` `#0d2b33` — both sampled off the TEST logo before
Jake delivered anything. They are `#30aac6` and `#282828` now, 5.40:1. The logo
was still 75px, sized for the taller header it used to live in; 52px on the
compact bar.

**"Today's Yoink" came out of the menu.** It pointed at `/`, which is where the
LOGO goes — so it duplicated the logo a few inches to its right, not the
announcement bar, which points at the deal PRODUCT page and is the only link
anywhere to it.

**Earning free shipping now looks like winning.** The cart had it backwards:
short of the threshold you got a message AND a progress bar; crossing it
suppressed the bar and left one line of 0.9375rem default-coloured text. The
best news in the cart was its quietest line. `won` is deliberately narrower than
`pct == 100` — the `flat` and `free` vendor shapes also sit at 100%, but those
are standing facts about a supplier, not something the shopper just achieved.

**The Bargain Bin's second row was ragged.** `auto-fill` let the column count
float with the viewport, so a wide desktop made six columns for eight products:
one full row, then two tiles beside four empty cells, which reads as a section
that failed to load. Fixed at two and four columns, both of which divide eight.
Keep `products_shown` a multiple of four. It also ends somewhere now — "See all
26" sits in the corner beside the heading, read before anyone has seen a
product; "Rummage through the bin" goes where browsing actually stops.

**The 404 is ours.** "Yoink" is a verb for snatching something away, so a missing
page has literally been yoinked — the rare joke that cannot be transplanted to
another shop. But the joke is not the point: a 404 is a customer one click from
leaving, so the page hands over today's live deal, priced, with its saving. It
resolves the deal itself by walking `daily_deal` for the window containing now,
exactly as `header-announcements` does, so it rotates at 9am with nothing to
edit and survives there being no live deal — which happens between runs and
would otherwise render an empty card at $0.

**THE THEME DEPLOYS ON `git push`.** The live theme is `project-aj/main`, which
is GitHub-connected, so a push to `afbohn/project-aj` IS the deploy. There is no
`shopify theme push` step and running one would fight the connection. Confirmed
by pulling the live theme and finding it already matched local.

**Where free shipping is called out**, since it came up: `blocks/aj-card-ships-free.liquid`
is wired into the collection, search, product, cart and 404 templates. It sits
beside the PRICE, not in the badge corner — that slot holds the discount, and
"Ships free" loses to "40% off" every time. It reads a real `draftOrderCalculate`
quote per product, not the vendor's usual behaviour. 329 of 2,048 products (16%).

## 3 August — the $40 that would have gone missing

**Closed test return #1011-R1 to prove the webhook, and found a defect instead.**

The good half first: the declarative `returns/close` subscription IS registered
and delivering. That had been unconfirmed all along — `webhookSubscriptions`
returns 0 for declarative webhooks and `shopify app versions list` came back
empty because the CLI is not linked to the real app, so neither check could
answer it. Closing a return did. The handler ran in 768ms and decided correctly.

**Then it refused to pay, and nothing said so.** The pure decision function is
stateless, so on close it re-derived `needs_approval` for a $40 return a human
had approved in the queue days earlier. Goods back, $40 owed, `return_decision`
written at `pending` — and `app.returns` read only `return_request`, filtering
on `status === "needs_approval"` while this record said `open`. The only trace
was a metaobject nobody opens. A real customer would still be waiting.

**Fixed as ONE approval, at the moment it means something.** Asking again at
close asks the wrong question: on Collective the goods go back to the SUPPLIER,
so a second approval judges something we never see. The queue now writes
`approved_at`, and settlement re-runs the pure function with the approval
ceiling lifted rather than hand-picking an action — so keep-it and
who-pays-postage keep working instead of being second-guessed at the last step.

`humanApprovedAt` returns null on ANY failure, deliberately. An unreadable
record means the return waits for a human; the opposite default would let a read
error authorise a refund. It matches on the Shopify return id, not order name —
one order can carry several returns, and approving the first must not silently
authorise the second.

**An automatic refund has to announce itself.** `sendSettlementNotice` mails when
money moves. The approval email says "decide", this one says "done", and sending
both is the point — an automatic settlement nobody is told about is a silent
success, and those are only discovered at reconciliation.

**The money is visible now.** `loadReturnsOverview` joins request to decision,
because neither describes a return alone and reading one in isolation is exactly
how this went missing. Both the dashboard and `/app/returns` render it. **"Owed,
unpaid" is the number that matters and it must stay at $0.00** — it means goods
came back and the customer was not paid. It renders critical whenever it is not
zero. Decisions with no request are kept: a return raised in the Shopify admin
never passes through our form, and dropping those would hide real money.

**Test data cleared**: order #1011 deleted, both metaobjects gone, no orders
tagged `internal-test` remain. The `TEST — Returns Harness` product and the
customer record were left alone — the first is the harness for future tests, the
second is Alex's own address, not test data.

**THE LESSON, because it is the third time.** The bug was not in any of the code
that was reviewed and tested; it was in the SEAM between two correct halves. The
queue was right, settlement was right, and nothing joined them. Same shape as
the 13 orphaned category collections the day before: created correctly, surfaced
by nobody. Whenever two records describe one thing, something has to read both.

## 3 August, later — verified on a real screen, and the numbers behind the vendor question

**The returns fix works.** Reproduced yesterday's exact failing case end to end:
$40 order, return requested through the live storefront form (`needs_approval`,
correct), approved with `approved_at` written, then closed. Result:

    [RETURNS_CLOSE] rd-57409011814 refund_cash — Approved by a human on
    2026-08-03, so the close settles it rather than asking again.
    [RETURNS_CLOSE] PAID $40.00 — refund gid://shopify/Refund/1150877761638

Refund created automatically, decision `paid`, dashboard "Owed, unpaid" back to
$0.00, no settlement-notice failure in the log. Test data cleared afterwards.

**The nav was over budget the day the tracking was added.** Measured live rather
than guessed: the menu column is 398px at 1920 and 338px on a laptop, while the
three labels needed 418px. It only rendered because `overflow-list` tolerates a
few pixels; below that it folded "Shop by category" into "More", hiding all 27
category links behind a word that names none of them.

Dropping tracking from 0.07em to 0.02em recovers ~37px and is NOT enough — at
338px the same labels still need 392px. The labels had to shorten. "Prices" and
"Categories" bring it to 251px: 87px of headroom instead of a 54px overrun.

**THE CENTRED LOGO IS THE REAL CONSTRAINT.** It fixes the left column at a third
of the bar regardless of content. If the nav ever needs a fourth item, move the
logo left rather than shortening labels again.

**Seen rendered, finally**: the 404 (hero, live deal, escape tiles, search), the
six price tiles, and the cart's earned free-shipping row — yellow `rgb(255,224,0)`
carrying ink, bar correctly suppressed. One real bug found by looking: the 404
was upscaling the deal image from its served 240px to a 418px box, blurry, and
forcing the card to 470px tall against 141px of content. Capped at 220px.

## Vendors — the data exists, the sales data does not

Asked whether an agent should score vendors on sales, stock, shipping and
returns. **0 orders and 2 customers**, so sales and returns are empty and stay
empty until traffic. The rest is rich: 71 vendors, unit cost on all 71, shipping
measured on 67, plus oos and no-ship tags.

**A first pass got this badly wrong and the correction is the point.** Subtracting
full shipping from margin reported 22 vendors and 508 products as loss-making.
Shipping is PASS-THROUGH — `margin.ts` is explicit that the customer pays the
carrier rate and we hand the same number to the supplier, so only the 2.9% fee on
the shipping line touches us. Corrected with the code's own `netKeep`:

    vendors whose median unit loses money      0
    products that lose money at list price     7 of 2,143
    catalogue median net keep per unit         $9.79
    vendors keeping under $3 per unit         12  (272 products)

The catalogue is healthy. The real finding is the thin tail — Ralphie's Funhouse
keeps $0.41 a unit across 48 products, Sticker Fire $0.83, Bear Dice $1.26 —
against White Water Life at $36.15 and Decorotika at $56.53. Thin vendors cannot
absorb one return, let alone a CAC.

**AND THIS IS THE META ANSWER.** $9.79 median contribution against cold paid CAC
of $25–60 means the first order loses money and needs repeat to recover, with 2
customers and no list to retarget and a pixel needing ~1,000 events to optimise.
The pixel itself is live and correct (`facebook_pixel`, id 1405178831488903,
`share_all_events`, `dataSharingState: optimized`), and the deal picker already
refuses to schedule below a margin floor that includes shipping and fees. The
blocker is arithmetic, not engineering.

**Seven of nine agents are supply-side.** lifecycle, catalog, bargain-bin,
invariants, enrich, shipping, digest all tend the catalogue; only meta and teaser
face demand, and meta is paused. More catalogue agents will not fix that.

## 3 August — the supplier scorecard, agent number ten

`vendors`, daily, pausable, at `/app/vendors`. Ranks all 72 suppliers on unit
economics, stock reliability, shipping shape and catalogue depth, and writes one
`vendor_score` metaobject each. **READS ONLY** — it changes no product, price or
collection. Dropping a supplier has contractual consequences, and an agent that
could unpublish 48 products because a median moved is a hazard, not a report.

**It states what it cannot see.** Zero orders means sell-through and return rate
are absent, so every score carries `confidence: unit economics only` and the
sales fields are optional, filling in on their own once orders exist.

**Net keep comes from `margin.ts`**, never a local formula — two definitions of
profit is precisely how the earlier "22 suppliers are loss-making" error
happened.

**Shipping shape is scored by its effect on AOV.** `scaling` ranks BELOW an
unreachable threshold: rising rates actively punish a bigger basket, while an
unreachable threshold merely fails to help. AOV is the lever the model rests on.

**Both verdict thresholds were tuned against real output, not guessed.**
"Carry more" first shipped at composite >= 70 and labelled 29 of 72 suppliers —
40% of the roster, a list rather than a recommendation. Raised to the top ~15%
with a separate dollar floor, since range only compounds if each extra unit is
worth selling. First real run:

    12 carry more | 46 keep | 8 drop candidate | 6 watch
    72 suppliers, 2,591 products, 25.7s

    carry more, top:  S And B Enterprise  $26.23/unit  free    48 products
                      White Water Life    $36.15/unit  46.3%   48 products
                      Sweet Bamboo        $15.93/unit  40.8%  331 products
    drop candidates:  Sticker Fire        $0.83/unit across 48 products
                      The Fidget Games    50% of range has no shipping rate
                      Ralphie's Funhouse  $0.41/unit across 48 products

A new agent defaults to PAUSED — `isAgentEnabled` returns false with no setting
saved, so the first run answered `dry: true`. The `agent-vendors` metaobject is
now `enabled: true`.

## 3 August — the free-shipping ask, and hashtags

**The number was the least visible thing in the block.** "Add $28.00 more from
Aura by Gem for free shipping" was one sentence of 15px body text, with the
figure that decides whether somebody adds another item set at the same weight as
the shipping policy beside it. Now 1.5rem purple in a bordered card above a
thicker bar. Purple, not the yellow the earned row uses: yellow is this brand's
"you got something", this is "here is something to do", and reusing the win
colour for an unmet target makes the real win mean less two seconds later. The
bar floors at 6% — starting empty tells someone who has spent $40 they have done
nothing.

**The upsell already knew which item closes the gap and never said so.** It runs
a three-tier pass that puts a threshold-clearing item first (with a dollar of
headroom, because the threshold is bisected to about a dollar). Then it rendered
that item identically to the two below it, so all the tiering achieved was
reordering three rows nobody could tell apart. It now carries "Adding this gets
you free shipping" in ink on yellow. **Third instance of the same failure this
week** — orphaned categories, the unpaid $40, and now this: work done correctly,
surfaced by nobody.

**Two bugs found by looking at the rendered cart, not the code.** First pass
badged all three suggestions — every tier-2 item clears, so a badge on
everything is a badge on nothing. Second pass still badged two: the vendor loop
runs TWICE for supplier fairness, so a boolean reset inside it let one supplier
badge again on the second pass. Now an accumulator keyed by vendor, like `seen`.

## Hashtags — relevance, not count

Deal captions ended with two static tags. The instinct at low reach is to add
twenty more and it is the wrong lever: Instagram has said plainly that hashtags
are no longer a meaningful reach signal, and a wall of thirty reads as spam to
whoever does see it. On Facebook they do close to nothing.

Five now, two or three derived from the product's own Shopify taxonomy, so a
skincare deal is tagged #skincare and findable by people who want skincare.
An explicit map rather than handleizing the segment — "Food, Beverages & Tobacco"
would become #foodbeveragestobacco, which nobody searches and which puts the word
tobacco on a post about hot sauce. Unmapped categories contribute nothing rather
than guessing. Costs one field on a query already running.

## 3 August — bin cards, and the Yoink selector was spending its best deals first

**The card stagger, in two wrong fixes and a right one.** Measured live: names
aligned at 1484px but prices split 1535 (no Ships free badge) against 1508 (with
one) — a 27px stagger across a four-up row, exactly one badge height plus the
gap. Cause was `margin-top: auto` on the price, which bottom-anchored it, so a
card without a badge let its price drop into the badge's space.

First fix reserved two lines of title height. That aligned the prices and
created a worse problem: four single-line titles meant four blank lines, and the
name-to-price gap read as a spacing bug. **Subgrid is the right answer** — these
are four independent grids sitting side by side, and spanning the parent's rows
makes media/name/price/badge share tracks ACROSS the row. Each track is as tall
as the tallest real content, nothing is reserved that is not needed, and the
badge row collapses entirely when no card in the row ships free. Verified: name
and price offsets identical on all four, gap down to 6px. `@supports` fallback
keeps the min-height where subgrid is unavailable.

## The Yoink selector — supply was never the problem

Asked whether there are enough products to be Yoinks. Measured:

    active                                  2,591
    in the bargain bin                         40
    oos / no shipping rate                    179
    no discount clears the margin floor       397
    stock under 25 units                      336
    QUALIFY                                 1,638   = 4.5 years of daily deals

**DEPTH IS THE SCARCE RESOURCE, NOT COUNT.** Only 145 of those 1,638 can go 40%
off and still clear the margin floor; the median has 19% of headroom. Deep
discounts are 9% of the pool — and the selector sorted by `maxDiscount`
descending, handing the deepest remaining deal to whoever planned that day,
every day. That spends the 145 best deals in about five months, after which
every remaining day is a sub-25% offer and the store's promise quietly degrades.

Nothing warned about it because from any single day's view the shortlist looked
excellent. Verified before the change: the shortlist was 25 deep candidates out
of 25. After: 4 deep, 11 mid, 10 shallow.

The shortlist is now stratified roughly 15/45/40, so reaching for a crown jewel
is a decision rather than the default. Bands fall back to each other, so a pool
with no deep candidates still returns a full shortlist. The margin floor, the
ship-ratio penalty and the vendor interleave are untouched.

**`minStock` 25 → 10.** The old bar excluded 336 otherwise-qualifying products to
guard against a Yoink selling out mid-countdown, which on a store with no
traffic was priced far too high. **This is the first number to raise again if a
deal ever does sell out inside its window.**

## 3 August — Ships free gets its own colour, and the coverage gap behind it

The badge was an 18% tint of the yellow on BOTH the PDP pill and the card badge,
which rendered as a pale grey smudge reading as neither badge nor benefit. The
deeper problem was the colour: yellow already means "you are getting a discount"
here, so dressing free shipping in a weak version of the saving's colour made it
look like a lesser saving rather than a different KIND of good news.

**Cyan was the one accent in Jake's palette doing no work.** Ink on cyan is
8.87:1 — better than most body copy on the site — so the fill is solid rather
than tinted. The old note argued a solid fill costs contrast; true of yellow at
1.34:1 on white, irrelevant to cyan. White on cyan is 1.66:1 and is never used.
One token in `aj-brand.css` drives both surfaces.

**THE BADGE WAS NEVER BROKEN — THE DATA IS MISSING.** A 48-card Home & Garden
page rendered zero badges, and the cause was not the badge: all 60 sampled
products had NO `ship.cost` measurement at all.

    active products                     2,591
      with a shipping measurement       1,837   (70%)
      of those, ship free                 410
      NEVER MEASURED                      754   (29%)

    unmeasured, by vendor:  Sweet Water Decor 447, Noble Otter 48,
                            Spongelle 48, Texas Salt Co 40, Sweet Bamboo 29

Sweet Water Decor alone accounts for 447 of the 754, which is why Home & Garden
looks badge-free. Measurement dates cluster on 31 July (1,385) with a long tail
since, so the shipping agent is working through it — but at ~250 a day the tail
is weeks, not days, and every unmeasured product is one that cannot show the
badge, cannot enter the Ships Free collection, and is scored on a guess by the
vendor scorecard.

**Worth a look next:** collection-page cards still stagger their prices when
titles wrap to two lines. The bin section was fixed with subgrid; the theme's
own product card has the same problem and was not touched.

## 3 August, afternoon — the preview send, and a supplier walking out

**Aura by Gem deleted us as a Collective connection.** Their products became
unsellable, Alex deleted them (correctly), and one of them was the live Yoink.
The metaobject kept its window, price and snapshot and pointed at nothing: the
deal section and announcement bar both vanished and the homepage opened on
empty space for about five hours. Traced through Shopify's event log — ten
destroys at 10:17:11–10:17:16 local, author Alex Bohn — rather than guessed.

The agents behaved correctly: `invariants` errored with "the live deal points at
no product", `meta` refused to post, `catalog` declined to hide anything on an
unreadable queue. Nothing was wrong except that nobody was told loudly enough.

**`healOrphanedDeal` now runs at the top of every lifecycle pass.** It
re-points, it does not re-price — puts an eligible product on the orphaned deal,
clears the activation fields, and lets `activateDueDeals` price it through the
identical path. Products already referenced by another `daily_deal` are
excluded, so healing today cannot empty tomorrow.

**Its selection was wrong first and had to be fixed live.** It took the
shallowest qualifying candidate — right instinct, wrong implementation, because
the minimum qualifying candidate has almost no headroom. It chose a planner
priced $34 against a $34 cost: a Yoink at 0% off with zero margin, which is its
own kind of broken homepage. Now: shallowest candidate carrying at least 25%,
falling back to the deepest only if nothing clears that bar.

**THE PREVIEW EMAIL EXISTS NOW.** The deal panel had collected addresses under
"know what it is before anyone else" since 30 July and tagged them
`yoink-preview`; nothing read that tag. Two senders: `customers/create` fires
immediately on signup (silence for eight hours is indistinguishable from a
broken form), and a nightly job at 19:00–22:00 store time covers everyone who
subscribed earlier. Real HMAC-guarded one-click unsubscribe plus
List-Unsubscribe headers — verified end to end, 200 on a valid token, 400 on a
bad one, consent restored afterwards.

**It must never quote a price the deal has not set.** Caught by Alex asking
whether tomorrow's product was discounted yet — it is not. A queued deal carries
`discount_percent` and an EMPTY `deal_price`; the lifecycle computes the real
figure at activation. The first send said "$30.00, save $30.00" for a deal
planned at 39% off. Price is null until `deal_price` exists and the mail leads
with the discount instead.

**Deals drop at MIDNIGHT, not 9am.** `starts_at` is 05:00Z. The announcement
bar fallback had been telling every visitor "A new Yoink every day at 9am", and
the same assumption had spread into snippet comments. Only visible because the
fallback was the only thing in the bar that afternoon.

**The deal image was sized by the supplier's photo.** `height: auto` meant a
tall spray bottle rendered ~1100px and towered over the content column. Square
box, `object-fit: contain`, capped at 34rem — every Yoink now occupies the same
space whatever shape it was shot in.

## API spend — mostly the build, not the agents

$35 over seven days, all Opus. Only two files call the model, and `ads-analysis`
runs solely when `/app/ads` is opened. The single recurring consumer is `enrich`:
one run a day, ~40 products in batches of ten, system prompt already cached.

The daily shape tracks build days, not agent runtime — $0 before work started,
$2.42 on a quiet day with agents running, $8–10 on heavy build days. That points
to roughly $2/day of agent against $6–8/day of us, and it is inference from the
pattern rather than a measurement.

**Give the Fly app its own API key** so the two never share a line again. Then
decide about `enrich` on Opus — it is classification against a controlled
vocabulary, and only the teaser line is real writing. Not worth optimising until
it can be seen on its own.

## 3 August, evening — the email programme, and two agents more

**THE SHAPE ALEX CHOSE.** One preview for anyone who asks at the deal panel,
one welcome then one weekly for everyone else, and the DAILY rhythm pushed to
social rather than to inboxes. "Send it to me" is a request for the next Yoink,
singular — reading it as a daily subscription would put words in somebody's
mouth and burn a domain with no sending reputation.

    yoink-preview  -> one preview, on signup, then done
    popup / list   -> welcome, then Thursday weekly
    daily habit    -> Instagram and Facebook

**The footer form had no tag at all.** Horizon's stock block, so everyone who
used it landed in the customer list indistinguishable from somebody who had
merely bought something — unmailable, and unrecoverable for anyone who signed
up before it was fixed. Tagged `list` now.

**`weekly`, agent eleven.** Thursday morning, idempotent on the ISO WEEK rather
than the day: a day key would let a failed Thursday fire on Friday, and a second
unrequested email is worse than a skipped one. Selection is a sort, not a
judgement, so it needs no model — the live deal plus the biggest bin savings.
Never a "what you missed" roundup, because expired deals have their prices
restored and every link would go to a full-price product.

**IT PICKED BADLY FIRST, AND THAT IS THE USEFUL PART.** The bin rotates at a
FLAT 25%, so ranking by percentage ties on everything and collapses to the
tie-break. Breaking toward cheapest produced two colourways of one ball holder
and "NUDE MALE BODY FIGURINE #2" — the three least impressive things in a bin of
38. Now ranked by DOLLAR saving (at a fixed percentage the biggest saving is the
most expensive item) with colourways deduped by title family, since Collective
syncs them as separate products.

**Marketing safety is now the email's own job.** 2,500 supplier products, none
vetted for what belongs in an unsolicited email. A deliberately over-eager word
filter plus a `no-promo` tag, applied to the hero, the bin picks AND the
bring-back titles. It will occasionally drop an innocent "nude pink" lipstick —
the right trade, because the bin holds 38 items and one wrong product in a
marketing email cannot be recalled. **The filter guards ONLY the emails: that
figurine can still reach the homepage, social, or the Yoink slot itself.**

**Vote counts order the bring-back list and are never shown.** "1 vote" reads as
nobody cares and talks somebody out of adding theirs.

**Social icons in every email**, served from the app's own host — Shopify Files
needs a scope that is Alex's to authorise, and a theme asset URL carries a
version hash that changes each deploy, which is a broken image in mail nobody
can re-send. Each sits beside a real text link with alt text, so Outlook's
default image blocking degrades to "Instagram · Facebook" rather than two empty
boxes. The Facebook mark is typeset: hand-drawing it produced a crossbar that
overshot the stem both ways, which is a plus sign, not an f.

**`?sample=` on both cron routes** sends either template to DIGEST_TO. Every one
of these renders differently in Gmail than in any preview tool, and the
alternative was creating a fake customer to fire the webhook — which is how two
sets of test orders and metaobjects got deleted by hand today.

## Shipping throughput doubled

754 products had no measurement. **The 45-second budget was never the
constraint** — the probe loop was strictly serial and each probe is a live
`draftOrderCalculate` round trip at ~4s, so 30 seconds bought nine products
while the wall clock sat idle. Concurrency 4 gave 32 a run and then threw
`Throttled`, losing the whole phase; two gives 18 and leaves headroom for the
agents that change things rather than merely learn things. A throttle is now a
SKIP, not an error — this is the only agent that spends calls to learn, so it is
the right thing to stop when the bucket is dry, and a red heartbeat for an
ordinary pause is how a monitor teaches you to ignore it.

## The deal card

Image was sized by whatever the supplier photographed — a tall bottle rendered
~1100px and towered over the content column. Square box, `object-fit: contain`,
capped at 34rem. And it has a gallery now: CSS scroll-snap so it swipes natively
without JavaScript, dots rather than thumbnails, arrows on desktop only behind
`(hover: hover)`. The only way to see a second photo used to be leaving for the
product page — away from the countdown and the buy button.

## ANSWERED — who bears return postage

**The supplier does. The $6.95 is margin, not recovery.**

Worked out rather than asked, from two facts that only mean something together:

Shopify's documentation gives three Processing modes and states plainly of the
one this store uses — *"Supplier creates label: The supplier provides and pays
for the return label."*

And the Default return policy reads **"30 days · No label fee · No restocking
fee"**. The label fee is what the RETAILER pays the supplier to compensate them
for creating the label; it is zero here. So the supplier creates it, pays the
carrier, and invoices us nothing.

**We incur no return postage cost.** Every prior note treating the $6.95 as cost
recovery was wrong, including the reasoning that justified introducing it.

**THAT MAKES THE COPY THE OPEN QUESTION, NOT THE ECONOMICS.** The storefront
tells a change-of-mind customer they are paying for return shipping. They are
not: they are paying a fee we keep, against postage a supplier absorbs. That is
lawful and ordinary, and it is not what the words say. Worth either renaming it
(a "return fee") or accepting the framing deliberately rather than by accident.

**CORRECTION — Customer refunds is now "Collective takes no action."** This file
recorded it as still set to "Automatically refund" on 2 August, flagged as an
error that sat under every returns decision for three days. Read from the app
again on 3 August: it has been changed. That is the setting the settlement path
needs — ours is now the only thing issuing refunds, so there is no double-refund
risk. Verified in the app, not inferred.

## 3 August, late — eight suppliers dropped, and two silent email faults

**THE EMAIL SIGNUP FLOW WAS DEAD, AND LOOKED FINE.** Asking "are we ready end to
end" found two faults, either of which alone meant every popup and footer signup
got silence:

1. `customers/create` was declared in `shopify.app.toml` and **never
   registered**. Declarative webhooks take effect on `shopify app deploy`, which
   was never run for it and CANNOT be from here — the CLI is not linked to the
   real app, which is also why `shopify app versions list` returns empty. The
   returns webhooks work only because they were added on 1–2 August when the app
   was last deployed. **Registered through `webhookSubscriptionCreate` instead.**
2. With the webhook arriving, the handler still exited in 23ms. **The
   `customers/create` payload carries NO tags** for a customer whose tags are set
   in the same call that creates them — exactly what the storefront forms do. So
   it saw a plain new customer and correctly ignored it. Tags are now re-read
   from the API when the payload has none.

Neither was visible in code: the route existed, the handler was right, the tag
branch was right, and nothing happened. Verified by creating a real customer and
watching it come back tagged `welcomed`. **If a webhook is ever added to the toml
again, it needs `shopify app deploy` or an API registration — the git push and
the Fly deploy do NOT register it.**

**Eight suppliers dropped**, 200 products set to DRAFT — reversible, off every
channel at once, and it keeps the `vendor_score` history that justified it.
Ralphie's Funhouse ($0.41/unit, 48), Sticker Fire ($0.83, 48), The Fidget Games
(50% unshippable, 44), Elijah's Xtreme ($1.64, 29), Books by splitShops ($1.47,
16), Bear Dice ($1.26, 10), Bards & Cards ($1.63, 4), Gotta Go Gotta Throw
($1.68, 1). Active catalogue 2,581 → 2,392.

**They are still connected in Collective**, so a sync could flip them back to
active. Disconnecting is a relationship action and is Alex's to do in the
Collective app.

The one apparent conflict was a false alarm: Gotta Go Gotta Throw's product is
attached to `daily-deal-azioo00y`, whose `ends_at` (28 July) is BEFORE its
`starts_at` (29 July) — the inverted-window record already on the Next list. It
could never have fired.

## The return fee, settled

**The supplier bears return postage; the $6.95 is margin.** Worked out from
Shopify's docs plus the Collective policy screen, not asked: Processing is
"Supplier creates label", which Shopify states means the supplier provides AND
pays for it, and Window and fees reads "No label fee" — what we would owe them.
Zero. Every earlier note calling it cost recovery was wrong, including the
arithmetic that introduced it.

Renamed throughout: `RETURN_SHIPPING_FEE` → `RETURN_FEE`, `returnShipping` →
`returnFee`, `wePayReturnShipping` → `weCoverReturn`. The
`we_pay_return_shipping` metaobject KEY is deliberately unchanged — renaming it
would orphan every `return_decision` already written.

**Free returns narrowed to DEFECTIVE and WRONG_ITEM.** `NOT_AS_DESCRIBED` now
pays the fee: it is a judgement only the customer can make, sitting in the
dropdown directly above "Changed my mind", and leaving it free made the fee
optional for anyone who read the list. A genuine case over $24.99 still lands in
the approval queue with the reason on it, so a human can waive it.

**Refund policy republished** to match: heading "Return fee", the free case names
exactly the two reasons that are free, and "we cover it — postage and all" is
gone because we do not pay postage.

## Purchasing — configured, never exercised

Store public, USD, Collective Carrier Service profile live, domestic rates,
Shop Pay/PayPal/Google Pay present. **But no real order has ever been placed** —
every order this store has seen was a draft order created by API and deleted.
Untested: a real checkout, tax at checkout, and above all **whether a paid order
syncs to Collective and gets fulfilled**. That last one involves somebody else's
system and is the biggest remaining unknown. One cheap self-purchase would
exercise all of it.

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

**From 1 August**

- **`setTimeout(fn, offset); setInterval(fn, period)` staggers only the FIRST
  run.** The interval starts counting at boot, so every job sharing a period
  converges on the same instants immediately after. Catalogue and shipping fired
  in the same second every 30 minutes and drained the rate-limit bucket
  together. It looked fine whenever anyone deployed, because a deploy
  re-staggers the first run. Nest the interval inside the timeout.
- **A zone offset derived from hour numbers breaks across a date boundary.**
  Right for 9am only because 9am UTC and 4am Chicago share a date.
- **A constant can be imported and never used, and nothing complains.**
  `PROMPT_VERSION` sat in the import list of the file that was supposed to hash
  it, for as long as the port has existed.
- **A cap on units attempted is not a cap on time spent** when each unit is a
  live third-party call.
- **Counting markup is not counting DOM.** Judge.me's app embed ships a large
  `<style>` block, so grepping the page for `jdgm-widget` matched CSS rules and
  reported a widget that was not rendered. Strip `<style>` and `<script>` before
  believing a count.
- **A literal Liquid tag inside a Liquid comment is still parsed.** A comment
  explaining which tag form to use, written with real tag syntax as the example,
  left an unclosed branch.
- **A displayed limit that nothing enforces is a false claim**, however
  carefully the code comment explains the intention. `units_allocated` was
  documented as "the allocation is what we will honour" and honoured by nothing.
- **A guard scoped to one product cannot see a collision between two.**
  `hasLiveDeal` was right about what it checked and blind to the case next door:
  two deals on one day, different products, both priced, one invisible.
- **A safety rule that reports a COUNT hides the thing it just saved.**
  `undoBatch` refused to delete a discounted entry — correctly — and said "1".
  Nobody can act on a 1. Name the product or the refusal is decoration.
- **The most expensive failure looks like a normal product page.** A stranded
  discount has no badge, no countdown and no tag; it is a listing at the wrong
  price. Sold-out and unshippable products at least LOOK broken.
- **A mirror only mirrors on the day you write it.** `candidates.py` was built to
  answer the same question as `candidates.server.ts` so the CLI could not
  disagree about money. The `oos` / `no-ship-rate` exclusions were added to one
  and not the other, and nothing anywhere fails when they drift.
- **`deal.py end` assumes the deal is running now.** It winds `ends_at` back to
  the current time, so pointing it at a future-dated entry manufactures an
  inverted window and leaves the snapshot behind.
- **`shopify store execute` authenticates as the Shopify CLI Connector App**, not
  as our app. It reports 24 scopes where the app has 183, so any scope check run
  through it describes the wrong application entirely. Ask the app's own token.
- **The stored session token is short-lived and expires.** Lifting it out of the
  session table works until it doesn't — one read succeeded and the next 401'd
  ten minutes later, because the row holds a token-exchange token that the app
  refreshes on request and nothing refreshes out of band. Mint one with the
  client-credentials grant instead.
- **A permanent failure answered with a 500 disables the webhook.** Shopify
  retries a non-2xx for 48 hours and then switches the subscription off, so
  "retry on every error" turns a missing scope into a handler that is silently
  dead for every future event.
- **App-declared webhooks never appear in `webhookSubscriptions`.** Topics
  declared in `shopify.app.toml` are managed at app level, so an empty result
  from that query is not evidence the subscription is missing.
- **No Shopify Function can raise a shipping rate.** Delivery customizations move,
  rename and hide; the only price operation on a delivery option is a discount,
  which reduces. Markup lives on `DeliveryParticipant`, not in a Function.
- **A flat handling fee would have falsified a live storefront claim.** 279
  products advertise free shipping keyed on a measured zero. Any fixed amount
  makes every one of those badges a lie at checkout. A percentage cannot.
- **Setting a theme token does nothing if the theme never renders that
  component.** The palette landed on `badge_sale_background_color` and the
  storefront did not change, because every badge on the homepage is a custom
  class in a section that draws its own tiles. Check the DOM for the class
  before assuming a setting reaches it.
- **Counting markup is not counting DOM — again.** `color-custom-badge-sale`
  appears four times in the page source and zero times once `<style>` and
  `<script>` are stripped. This is the second time this exact mistake has been
  made here; the first was a Judge.me widget that was not rendered.
- **A cap on units attempted is not a cap on latency either.** 64 sequential
  top-ups cost 7.7s not because any one was slow, but because they waited for
  each other. The same shape as the enrichment run that spent its whole budget
  on ten products.
- **A note in `result.errors` turns a healthy run red — the enrich edition.**
  Recorded here already for the catalogue sweep, and it happened again: one
  product missing from a batch of ten marked a run that enriched forty as
  FAILED 500. Write it down twice, apparently.
- **Alpha on a badge is a black-chip habit.** `rgb(... / 0.9)` softened a dark
  chip against a photograph; the same alpha over yellow washes it out and loses
  the contrast the ink text depends on.
- **Instagram cannot delete or replace published media.** No endpoint exists.
  A caption can be edited; the image cannot. Any rebrand mid-campaign is manual,
  post by post, in the app.
- **Facebook deletes only what the same app created.** Anything published by
  another tool, or by hand, answers `(#200) This post wasn't created by the
  application` and has to go through Business Suite.
- **The Meta system-user token cannot touch Page posts.** Derive a Page token
  with `GET /{pageId}?fields=access_token` first — the same distinction that
  once produced a "publish_actions deprecated" error for an unrelated reason.
- **A pixel face fails at feed scale before it fails anywhere else.** Instagram's
  profile grid renders a 1080 card at roughly 120px. Test type at the size it
  will actually be seen, not at the size it is authored.
- **A recorded intention is not a verified fact.** This file said automatic
  refunds were turned off on 31 July. They were still on when the Collective app
  was actually opened on 2 August, and every returns decision for three days was
  built on top of that. Had settlement been switched on, every cash return would
  have paid twice. Write down what you CHECKED, and re-check anything load-bearing.
- **A two-day SLA does not fail in sixty seconds.** Watching for a Collective
  return label for a minute and concluding it was broken was a measurement with
  no chance of succeeding. Read the setting before testing the behaviour.
- **`returnCreate` makes a reverse fulfillment order, not a label.** The label is
  the supplier's, uploaded on their schedule and synced by Collective.
- **Making every failure message identical also makes them undebuggable.** The
  return form answers the same thing whether the order is missing or the email is
  wrong, which is right for a customer and meant a genuine `!admin` failure would
  have looked exactly like a wrong email.
- **Shopify's order search index lags creation by seconds.** A lookup on a
  freshly created order legitimately finds nothing.
- **Shopify re-serialises `config/settings_data.json` and wins the merge race.**
  A commit changing that file AND an asset had its asset synced within minutes
  and its settings ignored for half an hour. Nothing was rejected — Shopify
  normalises the file's key order, commits it back to the repo, and a repo edit
  that has not been rebased onto that write-back simply loses. Pull, rebase,
  push again and it lands in seconds. The file is co-owned; Shopify wins ties.
- **Product card titles are `<h3 class="h4">`.** Verified in the live collection
  DOM. So ANY tag-level or preset-level heading rule — `h1, h2, h3` or `.h4` —
  puts a display face straight onto arbitrary supplier strings. Brand faces get
  listed selector by selector, or the next long title becomes three lines of
  parentheses in a novelty font.
- **A pixel font has no tabular figures.** Ohpixel gives "1" an advance of
  0.400em and every other digit 0.600em, and ships no `tnum` feature, so
  `font-variant-numeric: tabular-nums` has nothing to switch on. A two-digit
  group swings 0.400em, meaning a clock shudders every second. Pin the width.
- **A screen-reader label with no CSS prints on the page.** `.aj-past__gonelabel`
  and `.aj-past__nowlabel` said "discounted price" and "regular price" in every
  card because nobody ever wrote the rule that hides them.
- **...and clipping it can take the meaning with it.** Once hidden, the line was
  two bare numbers whose struck member was the LOWER one — which reads as a price
  rise. An accessibility label is sometimes carrying semantics the visual design
  was silently relying on.
- **`display: block` overrides the `[hidden]` attribute.** Styling a vote counter
  made every card announce "0 people want this back". Use `visibility` when the
  slot needs reserving, and remember the UA rule is only an attribute selector.
- **Margins on a gap-based layout double the spacing.** `.aj-past__item` already
  had `gap: 0.3rem`; adding `margin-block-start: 0.4rem` made every space
  0.7rem. Read what the section already declares before adding to it — the same
  mistake as putting the pixel face on a class without checking what it holds.
- **A later rule at equal specificity silently undoes `margin: auto`.** A blanket
  `> * + *` margin killed the `margin-block-start: auto` that was bottom-aligning
  every card's button, and nothing anywhere reports it.
- **A returned `Count` can be capped.** The Collective delivery profile reports
  500 variants against a catalogue of ~7,000. Rates demonstrably work, so this is
  near-certainly a display cap — but ask for `precision` before believing a count,
  because "a profile containing the wrong variants" is what broke checkout in July.

**From 31 July, night**

- **Shopify bills the connection size you REQUEST, not the one you get.**
  `variants(first: 100)` cost the same on a 3-variant product as a 100-variant
  one, on 1,503 products, in three agents, every half hour.
- **`first: 100` on variants truncates silently at 100**, and one product sits
  on exactly 100 right now. Ask `variantsCount` as well, or a short list looks
  identical to a complete one.
- **A note pushed into `result.errors` turns a healthy run red.** The catalogue
  sweep reported "completed variants for 55 products" as an error and the
  dashboard showed a failing agent doing precisely what it was built to do.
  Introduced while fixing the same class of bug an hour earlier.
- **A deliberate no-op still has to write a heartbeat**, or the dashboard
  reports the last time the agent DID something as the last time it ran.
- **A monitor that sends outside its window is worse than none.** The digest's
  first version checked `hour < 8` and would have mailed at 8pm, then every
  fifteen minutes. Bound both ends.
- **Unconfigured is not broken.** A missing credential reported as an error
  every tick buries the real errors the monitor exists to surface.
- **A literal Liquid tag inside a Liquid comment is still parsed.** A comment
  reading "use the plain if-tag, not the stripping one" — written with real tag
  syntax as the example — left an unclosed branch. theme-check caught it.
- **Scopes added in the Developer Dashboard do not reach `shopify.app.toml`,**
  and the next `shopify app deploy` reverts them without a word. Pull after
  changing anything in the dashboard.

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

**PICK UP HERE (4 August).**

**The blocker is Jake, not the store.** Final logos and brand assets are
outstanding, and pushing traffic to a placeholder logo spends attention that
does not come back. Whatever unblocks him is the critical path; everything below
is preparation.

0. **Place one real order yourself.** A few dollars exercises checkout, tax, the
   order-confirmation email, the Collective handoff and fulfillment in one go.
   No genuine order has ever been placed on this store — every one so far was a
   draft order created by API and deleted. Whether a paid order actually reaches
   the supplier is the biggest untested thing here, and it is somebody else's
   system.

**Then:**

1. ~~Verify the returns fix, fix the nav, look at the visuals.~~ **All three done
   3 August.** See the section above.
2. ~~Build the vendor scorecard agent.~~ **Built and running 3 August.** See
   above. Worth acting on its output: 8 drop candidates, and 12 suppliers worth
   asking Collective for more range from.
3. **Ask Collective who bears return postage.** Still unanswered, and it decides
   whether the $6.95 is cost recovery or margin.
4. **Decide the demand-side plan before spending on Meta.** The arithmetic above
   says cold paid buys expensive data, not customers, until AOV rises or there is
   a list. The two levers are already half-built: the cart knows each vendor's
   gap to free shipping and does not upsell into it, and the email popup captures
   to nothing.

Then the standing backlog below.

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
- **Turn `meta` on when the teaser campaign ends — around 9 August.** The queue
  was restarted from q1 on 2 August, so the runway is longer than it was.
- **Attribution gets real** from the first deal post carrying UTMs: Shopify
  Analytics → Sessions by UTM campaign.
- **Ads.** Everything so far is reversible; ad spend is the first thing that
  leaves and does not come back. Guardrails there need to differ in kind, not
  degree: a hard cap enforced in code, a spend ledger reconciled against Meta,
  campaign budgets set at Meta so the kill switch works when the app is down, and
  approval per campaign. Use `utm_medium=paid_social` so paid and organic sit
  side by side in one scheme.

  **And read the CAC arithmetic above before spending anything.** The model
  supports $6.69 CAC on realistic assumptions and $20.44 at its absolute ceiling.
  Cold paid runs $25-60. Ads are not the growth lever until AOV roughly doubles
  or there is a list to retarget — the guardrails matter less than the fact that
  the first cohort cannot be bought.
- **Grow AOV.** The single strongest lever in the model, and the mechanism —
  same-vendor items chosen to clear a free-shipping threshold — is already in the
  cart. At $35 CAC and 4 lifetime orders the model needs $82.71 AOV against
  $37.99 today.
- **A recurring "win today's Yoink" draw**, rather than a one-off giveaway. Costs
  one wholesale unit a week (~$70) and builds the daily-open habit the whole model
  depends on, instead of one spike of sweepstakes hunters. Needs official rules
  drafted, and needs the list warmed carefully — `hello@` has SPF and DKIM but
  zero sending reputation, and a low-engagement blast would burn the domain before
  the daily email ever matters.
- ~~Finish the returns branches before writing anything that moves money.~~
  **Done.** Twelve cases verified against the pure function, worst-reason-wins
  and multi-line valuation proven live, and `refundCreate` built and tested both
  ways.
- ~~Store credit.~~ **Built 2 August**, tested, off with everything else.
- ~~NOTHING WATCHES `hello@`.~~ **Largely solved.** Returns now start at the
  storefront form (`proxy.return.tsx`), land in the approval queue at
  `/app/returns`, and email a human the moment one needs a decision. The residual
  risk is only a customer who emails instead of using the form. Original note:
  no agent reads that mailbox — a return request sits there until a human opens it and creates the
  return in Shopify by hand. The webhook fires on the RETURN, never on the email.
  The morning digest does not mention returns either, so a `return_decision`
  written overnight is invisible until someone goes looking in the metaobject
  browser. Adding pending decisions to the digest is small and worth doing.
- ~~Decide whether to switch refunds on.~~ **`agent-returns-pay` is ON.**
  Verified live on 2 August (`enabled: true`), not inferred from code. This entry
  said "it is off" for a day after it had been turned on, which is the same class
  of error as the automatic-refunds line that sat wrong under every returns
  decision for three days. CHECK THE METAOBJECT, NEVER THIS FILE.
