# Where things stand

Snapshot at the end of 30 July 2026. Written so tomorrow starts from facts
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
more than it did before, because it is where all seven agents live.

## The seven agents

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

1. **Deals run out 8 August.** Nothing is queued past it, and the homepage
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
- **The policies are drafted but not published.** See the shipping/returns
  section — this is the largest open exposure on the store, and it is a paste.
- **Search & Discovery filters are not wired to the new metafields.** The
  definitions are filterable; making a filter appear is a manual step in the
  Search & Discovery app.
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

## Shipping and returns — NOT settled, and this is the live exposure

The 30 July review of the actual store found three things wrong. Replacement
text is drafted at `docs/policy-drafts.md`, **and none of it is published yet**
— the app has no `write_legal_policies` scope, so it is a manual paste.

1. **There is no shipping policy page.** `/policies/shipping-policy` 404s. On a
   ~40-vendor dropship store this is the highest-risk gap on the site.
2. **The refund policy is unedited boilerplate.** It publishes
   `[INSERT RETURN ADDRESS]` literally, lists `abohn@onecountry.com` instead of
   `hello@theyoink.com`, and promises "we'll send you a return shipping label" —
   committing to merchant-paid returns on every order, to one address, on a
   store whose goods ship from forty vendors.
3. **Free shipping over $70 was attached to a profile containing zero
   products.** Every product sits on the Shopify Collective profile with
   carrier-calculated rates, so the threshold never applied to anything and the
   cart upsell it was meant to drive did not exist.

**Canada and International delivery zones were deleted** on 30 July. Both
profiles are US-only now. Settings → Markets still needs checking by hand — the
app has no `read_markets` scope, and if Canada is still an active market
shoppers there reach checkout before discovering nothing ships.

Decided: **nothing is final sale**, **14-day return window**, customer pays
return shipping, no restocking fee, delivery quoted as *5-10 business days, up
to 15*. Transit damage is a 48-hour window; **defects stay at 30 days on
purpose** — narrowing that does not reduce exposure, it converts it into
chargebacks, which is worse.

The vendor-variance problem has an answer that is not a number: **you are the
merchant of record**. Vendor terms decide how much you *recover*, not what you
*owe*. Set the customer window where it converts, treat recovery as a cost line,
and triage internally — under ~$25, refund and let them keep it, because return
shipping costs more than the item is worth.

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

- `sections/*-group.json` is owned by the theme editor; repo edits are ignored.
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
