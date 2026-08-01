# Agent brief — The Yoink, marketing & growth

**Reconciled against live store state, 1 August 2026.**

Tags: `[VERIFIED]` measured against the live store or API on the date shown ·
`[CORRECTED]` the previous brief said otherwise, and was wrong · `[OPEN]`
genuinely unresolved — never resolve one by guessing, surface it and stop.

**What changed in this pass:** five of the previous brief's eight open items are
closed, two of its factual premises were wrong in ways that would have produced
losing decisions, and three things it treats as existing do not exist. Sections
that were right are preserved with their reasoning intact.

---

## 0. Business context

- Shopify store selling one deeply discounted deal per day (the Yoink), plus a
  persistent catalogue.
- All inventory sourced via **Shopify Collective**.

**`[CORRECTED]` There are ~50 suppliers, not four.** 1,551 products across 50
vendors as of 1 Aug, growing — 48 arrived overnight. The four with documented
margins are real and exact but **not representative**:

| | |
|---|---|
| Documented four | prodigalpottery 50%, Blessed Bayou 50%, Gotta Go Gotta Throw 40%, Shield Your Body 30% |
| Catalogue median | **40%** |
| Below 30% margin | **34.7% of costed variants** |
| Thinnest vendors | Miller Bison **10%**, Bear Dice **10%**, Intelligent Change 15%, Wags & Whiskers **16%** (189 variants) |

Measured across 10,593 costed variants. **Any rule that assumes "margin ceiling
is 30–50%" loses money on a third of the catalogue.** A 10%-margin product
breaks even at roughly a 5% discount — it cannot carry a Yoink at all, and it
cannot carry a bundle discount or a creator commission either.

- The daily deal is priced at or near cost. **Margin comes from the rest of the
  cart, not the deal.**
- The model depends on returning daily visitors, not one-time acquisition.

---

## 1. Hard rules — never violate

Unchanged from the previous brief; all still hold. One addition and one
sharpening.

1. **Never price below cost.** `[CORRECTED — the rule was necessary but not
   sufficient]` The clamp is to unit cost, and the 2.9% + $0.30 processing fee
   sits *outside* it. "Max discount equals the supplier's margin" is wrong by
   the fee in every case: true break-even is 43.6% on a $9 ornament, not 50%.
   The floor is measured **net** now — see `decisions.md`.
2. **Never fabricate urgency.** Countdowns target real absolute timestamps;
   claimed bars derive from real inventory.
3. **Compare-at must be a genuine former or MSRP price.**
4. **Never promise combined shipping** unless every item is from one supplier.
5. **Never state a delivery date.** Describe shape ("ships separately"), never
   a date.
6. **Never change the inventory location on a Collective-imported product.**
   `[VERIFIED]` Breaks order syncing and causes fulfilment failures.
7. **Never post promotional content to Reddit or Slickdeals** from a brand or
   fresh account.
8. **Never display a supplier's review as if it were ours.**
9. **NEW — a cost argument may decide logistics and must not decide an
   obligation.** Cheap-to-recover reasoning may decide whether we ask for an
   item back; it may not decide whether we owe someone their money. See the
   returns section in `decisions.md`.

---

## 2. Email and messaging

### `[CORRECTED]` The prerequisite is met — sending is unblocked

The previous brief listed SPF and DKIM as `[OPEN]` and said they block all
sending. Both are live and verified by `dig` on 1 Aug:

```
SPF     v=spf1 include:_spf.google.com ~all
DKIM    google._domainkey, 1024-bit (the size that fits Shopify's 255-char field)
DMARC   v=DMARC1; p=none
MX      smtp.google.com
```

`hello@theyoink.com` is a real mailbox with its own app password, and has been
sending automated mail since 31 July. **The domain is authenticated. Marketing
sending is not blocked.**

One real gap remains: **DMARC has no `rua=` reporting address**, so there is no
visibility into deliverability or spoofing. Add
`v=DMARC1; p=none; rua=mailto:hello@theyoink.com`, watch for a few clean weeks,
then tighten to `quarantine`. Tightening first is how you discover you were
blocking your own mail.

### System map `[VERIFIED]`

| Touchpoint | Location |
|---|---|
| Welcome, abandonment | Shopify Messaging → Automations |
| Order confirmation, shipping | Settings → Notifications |
| Weekly recap | No native recurring dynamic campaign — build from `daily_deal` metaobjects |

### Task: transactional templates — highest priority

Unchanged and still the top item. Multi-supplier orders produce multiple
fulfilments, so one order fires several shipping confirmations each listing
partial contents.

- Order confirmation: state that items from different makers ship separately;
  name the makers.
- Shipping confirmation: say this is one of several shipments where applicable.
  Never imply completeness on a partial fulfilment.
- No dates anywhere.

### Task: welcome flow — 2 emails

- **Constraint holds: no discount code.** The Yoink is at cost.
- Email 1 (immediate): what the store is, the daily cadence as an explicit
  expectation, offer web push as an alternative channel.
- Email 2 (+48h): Bargain Bin and browsing by price or category. **Not
  bundles or themed collections — see §3.**

### Task: abandonment

- **Set wait to 45–60 minutes.** `[VERIFIED]` Default is 10 hours, which
  routinely sends after the deal expires.
- Condition against the deal's `ends_at`. **An email must never advertise an
  expired price.**
- `[VERIFIED]` No abandoned-checkout email sends to a customer who has not
  purchased and is not subscribed. Low early volume is expected, not a bug.
- Prioritise abandoned product browse — the daily deal page is effectively the
  whole store.

### `[CORRECTED]` Channel note

The previous brief preferred web push "on a young unauthenticated domain."
The domain is authenticated now, so that argument no longer applies. Email and
push are both viable; the choice is a product decision, not a deliverability
constraint. `[OPEN]` — still a human call.

**Email capture now exists on the deal page.** Until 31 July it was footer-only
with nothing offered in return. The sneak-peek block on the homepage and PDP
now asks for an email in exchange for early notice of tomorrow's Yoink, tagging
subscribers `yoink-preview`.

---

## 3. Bundles

### `[CORRECTED]` "Chef's Kiss Bundles" does not exist

Nor do themed collections. Of 80 collections on the store, the named ones are
**Bargain Bin (26 products)**, 48 vendor collections, 5 price bands, and
category collections. The previous brief refers to bundles and themed
collections as existing surfaces — in the welcome flow, in the voice rules, and
in §8's naming decision. **They are proposals, not inventory.**

Treat this section as a build spec, not a maintenance guide.

### Rules for when they are built

- **Default: one supplier per bundle.** Fixes shipping, inventory stability and
  returns simultaneously.
- `[VERIFIED]` Collective works with Shopify Bundles, Flow and Subscriptions.
  Not with Managed Markets, POS in-person fulfilment, digital products, gift
  cards.
- **Use the native Bundles app only.** Third-party bundle apps read and write
  component inventory across locations and will violate hard rule 6.
- **Shipping economics** `[VERIFIED]`: overriding a supplier's rate to show free
  shipping still leaves us owing them their rate. If the *supplier* configures
  "free over $X" in their price list, we pass it through at no cost. Only design
  around the second.

### `[CORRECTED]` Thresholds are measured, not open

The previous brief marked supplier free-shipping thresholds `[OPEN]` and said
bundle composition was blocked on them. They were measured on 31 July and are
live in `vendor_shipping` metaobjects, projected onto every product as
`ship.vendor_shape`, `ship.vendor_free_threshold`, `ship.vendor_reachable`:

| shape | n | meaning |
|---|---|---|
| threshold | 25 | free above a cart value — median **$84** |
| scaling | 9 | gets **more** expensive per item — never upsell these |
| free | 9 | $0 at every quantity |
| flat | 5 | same rate however many items |

**Six of the 25 thresholds are unreachable** by their own catalogue — August
Uncommon Tea is free above $56 and sells one $14 product. Reachability is a
measured field, not an inference. **Bundle composition is unblocked.**

### `[CORRECTED]` Unit cost populates

Marked `[OPEN]`. Verified: **10,593 costed variants**, only 10 without cost.
Hard rule 1 is enforceable. Still worth re-checking on *bundle* products
specifically once any exist, since a bundle is a new product record.

### Remaining bundle rules

- **Discount depth is per supplier, never store-wide**, and must sit under that
  supplier's *measured* margin — which for a third of the catalogue is under
  30%, and can be 10%.
- **A bundle must never be the daily Yoink.** Three items at cost is triple the
  cash burn, not triple the margin.
- Bundle availability is set by the lowest-stock component; supplier stockouts
  silently take bundles offline. Monitor and report.

---

## 4. Reviews

- **Store-level reviews matter more than per-product reviews here.** The daily
  deal rotates out, so per-product equity never compounds on the converting
  item. The visitor's question is whether the store is legitimate.

### `[CORRECTED]` Judge.me is wired — the gap is reviews, not UI

The previous brief and `state.md` both said no review UI was wired into product
cards or the PDP. Verified on the live storefront, 1 Aug: `jdgm-widget`,
`jdgm-rev` and `jdgm-carousel` render on the PDP, and `jdgm-prev-badge` renders
on collection cards.

**Both were right when written.** The review-widget block was added in the theme
editor on the morning of 1 August, which is also why it does not appear in any
commit — the editor writes back to `product.json` directly. Check the live page,
not the repo, and strip `<style>` before counting: Judge.me's app embed ships a
large stylesheet whose rules name every one of those classes, so a naive grep
reports a widget on pages that render none.

`number_of_reviews: 0`. **You cannot wire your way to social proof.** The
constraint is that the store has no orders, so it has no reviews. That is a
consequence of having launched, not a task.

- `[VERIFIED]` Collective does not sync reviews. It syncs product attributes
  only.
- `[VERIFIED]` Reviews are a Collective *discovery* signal in the other
  direction — suppliers evaluating us can see our average rating.
- If importing supplier reviews by CSV: product-quality reviews only, strip
  anything about shipping or service, label the source visibly. Never present
  them as reviews of us.

---

## 5. Acquisition

### `[CORRECTED]` The gate has moved — the margin question is answered

The previous brief blocked all paid spend on two unknowns: contribution margin
and the supplier returns policy. Both are now known.

**Contribution margin, computed on real costs:**

```
contribution = D(1 − 2.9%) − C − 2.9%·S − $0.30
```

Shipping is pass-through but not free — we pay 2.9% of what we collect.

| Net floor | Breakeven ROAS |
|---|---|
| 5% | 20.0× |
| **10%** | **10.0×** |
| 15% | 6.7× |
| Undiscounted sale | 2.2–4.0× |

**This does not gate paid spend pending data. It rules out buying orders for
the deal product.** Meta or Reddit cold traffic does not return 10×; it does not
reliably return 3×. That is "this loses money," not "this earns less than the
alternative."

**Supplier returns policy** `[VERIFIED]` — Collective's current default:
supplier creates the return label, 2-day processing, 30-day window, no label
fee, no restocking fee. Automatic refunds were turned **off** on 31 July so
keep-it-and-credit remains possible; refunds are consequently ours to issue.

### What is still genuinely open

- **`[OPEN]` Attach rate.** Zero orders, so unmeasured. This is the number that
  decides whether a first order is worth more than its own margin — and
  therefore whether paid acquisition is ever viable here. Re-run this section
  after ~30 orders.

### What paid spend should target instead

**Cost per email, not cost per order.** An email pays off across every future
deal; an order at a required 10× ROAS does not pay off at all. The value of an
email is itself unknown until repeat rate exists — name that assumption, don't
build on it.

**Before any spend, three things must be true.** Verified state as of 1 Aug:

| | |
|---|---|
| Meta pixel + CAPI | ✅ live — `1405178831488903` via the sales channel, domain verified |
| Storefront password off | ✅ |
| Email capture on the deal page | ✅ as of 31 July |
| Deal calendar runs 30+ days | ✅ full through 31 August, gap-free |
| Reviews on the storefront | ❌ zero |
| Brand assets landed | ❌ logo exists, full brand pending |

The pixel has **zero purchase events**, which is exactly why cold traffic must
optimize for email signup rather than Purchase.

### Shopify Collabs — still the preferred first channel

- `[VERIFIED]` Available on all plans except Starter and Retail, no minimums,
  ~2.9% on automatic commission payouts.
- `[VERIFIED]` The Collabs *Network* additionally requires a completed brand
  profile, auto-payments, ≥$10K trailing-year sales, and not being a
  dropshipping store.
- `[OPEN]` Whether a Collective retailer counts as "a dropshipping store" is
  unresolved publicly. **Do not assert either way.** Ask Shopify in writing
  when approaching $10K.
- **Set commission at collection level and exclude the daily deal** — and now
  also exclude the sub-20%-margin vendors, since a commission on a 10%-margin
  product is a loss.
- Seed the *format*, not a product: the product expires before content ships.

### Paid ads — later, and Reddit first when it happens

- `[VERIFIED — third-party benchmarks]` Reddit CPMs run materially below Meta,
  and supplier verticals map cleanly to subreddits.
- `[VERIFIED]` Reddit floor is $5/day, but conversion campaigns need ~50 events
  to exit learning; budget $30–50/day for a real test.
- Narrow subreddit targeting (<100K members) pushes CPMs up.
- **Creative must sell the format, not the day's deal.** A 24-hour deal cannot
  survive ad review plus learning phase.

---

## 6. Apps

**Install / finish (all free):** Shopify Messaging, a web push app, Search &
Discovery — the last to expose the existing `cat-*` and `band-*` tags as
filters, plus the newer `enrich.hero_score` and `enrich.color` metafields, which
are definition-backed and filterable but not yet surfaced.

`[CORRECTED]` Judge.me needs no further wiring — see §4.

**Do not install:** SEO apps, trust badges, spin-to-win popups, and especially
"sales pop" / recent-purchase tickers — the last violates hard rule 2.

**Print-on-demand: not now** — but see the merch note below, which is a
different thing and is already built.

### `[NEW]` Own-fulfilment merch — plumbing exists, product does not

A cart tier for products **we** fulfil is live and renders nothing until the
`yoink-merch` collection has a product in it. It sits outside the shipping
threshold logic on purpose: we post merch ourselves, so it always adds a parcel
and can never clear a supplier's threshold.

The economics are the inverse of the catalogue — a $5 sticker set nets ~$3.42
after print, envelope, stamp and fees (**68%**, against a catalogue median of
40%), which makes its breakeven ROAS ~1.5× rather than 10×. Two operational
constraints: it needs a delivery profile at our own location or the catalogue
agent will unpublish it for having no shipping rate; and "envelope and a stamp"
only holds for flat goods — koozies and mugs are parcels with different maths.

---

## 7. Community and organic

Unchanged — all still holds.

- `[VERIFIED]` Slickdeals prohibits retailers and their associates from posting
  their own deals. Alternate accounts get flagged, suspended, then banned.
- `[VERIFIED]` Reddit enforces a ~90/10 participation-to-promotion norm;
  subreddit rules override sitewide policy; brand AMAs generally need moderator
  pre-approval; some subs ban brand accounts outright.
- **Deal-aggregator communities are a poor fit.** They price against verifiable
  SKU history our catalogue lacks, and produce single-purchase buyers when the
  model needs repeat visitors.
- **Better targets, in order:** (1) our suppliers' existing customer bases,
  (2) vertical communities per supplier, (3) "cool finds" newsletters and gift
  guides, (4) fans of the daily-drop format.

`[CORRECTED]` "our four suppliers' existing customer bases" — there are ~50, and
the largest by catalogue share are Sweet Bamboo, Wags & Whiskers, Sustainable
Village and Runic Dice. Target by *audience fit*, not by the four whose margins
happened to get written down first.

---

## 8. Naming — pending human decision `[OPEN]`

**Recommended: The Stalls.** Scales per niche (The Candle Stall, The Pottery
Stall), reads instantly, gives open/closed language for rotation, sits alongside
Bargain Bin without competing.

Alternates: Side Quests, Corners, Yoink Nooks, The Loot Table. Rejected:
anything using "Piles" — undercuts *curated, not cheap*.

`[CORRECTED]` Note the thing being named **does not exist yet** (§3). This is a
naming decision for unbuilt surface, which is fine — but it is not blocking
anything currently shipping, and should not be treated as urgent.

**Do not implement until a human confirms.**

---

## 9. Voice rules for any generated copy

Unchanged, with one correction.

- Use freely: deal, score, loot, snag, yoink (verb), lucky find, big score,
  drop, today only, gone tomorrow, treasure, haul, zap, zany.
- Avoid: discount, sale, clearance, cheap, markdown, blowout, "limited time
  offer", "don't miss out", "amazing", "incredible".
- "Bargain" only inside "Bargain Bin". `[CORRECTED]` The rule reserving
  "Bundle" for "Chef's Kiss Bundles" has nothing to reserve it for yet — treat
  it as reserved for whenever bundles ship.
- Short sentences. One emoji maximum, and it is ⚡.
- Deal post formula: hook → what it is → the value → the nudge. Lead with the
  product, state the real number, end on the clock.
- Gut check: does this sound like a friend with great taste tipping me off, or a
  store trying to move inventory? If the second, cut the hype and shorten.

---

## 10. Open items requiring a human

The previous brief listed eight. Five are closed.

| # | Item | Status |
|---|---|---|
| 1 | Do Collective suppliers credit returns? | ✅ **Closed** — current default: supplier creates label, 30-day window, no restocking fee. Auto-refund now off by choice. |
| 2 | What is our attach rate? | ❌ **Open** — zero orders. Still the number that decides whether paid acquisition is ever viable. |
| 3 | Supplier free-shipping thresholds | ✅ **Closed** — 25 measured, median $84, 6 unreachable. |
| 4 | Does unit cost populate? | ✅ **Closed** — 10,593 costed variants. Re-check on bundle products when they exist. |
| 5 | SPF and DKIM | ✅ **Closed** — both live. Add a DMARC `rua=` for visibility. |
| 6 | Name for the themed collections | ❌ **Open** — and not blocking; the surface is unbuilt. |
| 7 | Email, push, or both for the daily drop | ❌ **Open** — now a product choice, no longer a deliverability constraint. |
| 8 | Brand assets | ⚠️ **Partial** — logo exists (purple `#814a9e`, yellow `#ffde00`, cyan `#43afca`, measured). Yellow fails contrast as text at 1.34:1 and can only be a background. Fonts and licence still open. |

### New items this brief adds

| # | Item | Why it needs a human |
|---|---|---|
| 9 | **6 ACTIVE variants priced below cost**, all Wags & Whiskers, worst $58.99 against a $62.15 cost | Losing money at full price. The fix is a supplier price or dropping the line. |
| 10 | **1 product serves `og:price:amount = 0.00`** to Meta and Instagram link previews | The card shows $40 correctly; the machine-readable price is $0.00. Sets a price on one empty variant. Fix before `meta` comes off pause. |
| 11 | **Sub-20%-margin vendors in commission and bundle scope** | A creator commission on a 10%-margin product is a loss. Needs an exclusion rule. |
| 12 | **`returns/close` pays nothing yet** | The handler decides and records; execution needs a human to switch on, and there are no orders to test it against. |
