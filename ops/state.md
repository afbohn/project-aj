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

## The nine agents

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

1. **The calendar is full through 31 August** — 8 to 31 August scheduled in one
   batch, `batch_id: plan-aug2026fill`, no gap between today and the 31st. The
   earlier note here said 7 August was empty; it was not, and the queue is no
   longer eight days deep. **The runway is now checked by the invariants agent**
   rather than by someone noticing, so this should never again be a thing to
   look at by hand.
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
label fee, no restocking fee, declined returns auto-cancel.

**Automatic refunds are OFF as of 31 July.** This was the single setting that
decided whether a custom refund policy was buildable at all: with it on,
Collective processes the refund itself the moment a return closes, and no
keep-it-and-credit logic can ever run because there is nothing left to decide.
With it off, refunds are ours to issue on the `returns/close` webhook. The cost
is real — every accepted return now needs someone or something to actually
refund it, and a return that closes with nothing listening is a customer who
does not get their money back. **Nothing listens yet.** That handler is the
next thing to build, and until it exists refunds are a manual step.

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

1. **`write_orders` is granted, so the returns handler COULD refund.** It still
   does not. Switching it on is deliberate, and belongs with a human watching.
2. **There is still no store-credit scope.** `write_store_credit_account_transactions`
   is absent, so keep-it-and-credit — the entire reason automatic refunds were
   turned off — cannot execute even now. Cash refunds could; credit cannot.

**62 of the 72 scopes are referenced nowhere in `app/`,** and eleven carry real
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

### Corrections to earlier entries

- **Judge.me IS wired now.** This file said no review UI was wired; that was
  true until 1 August, when the review-widget block was added in the theme
  editor. It renders on the PDP and on collection cards. `number_of_reviews` is
  0 — the gap is having no orders, not missing UI.
- **The scheduler's stagger only ever applied to the first run.** See below.

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
