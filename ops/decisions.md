# Decisions and why

Things that are not obvious from the code, recorded so they do not get
relitigated or accidentally undone.

## Urgency is real, never synthetic
The countdown targets an absolute UTC timestamp from the deal's metaobject, so
it is identical for every visitor and does not restart on refresh. The claimed
bar is computed from real inventory. Fake countdowns and random "% claimed"
bars are an FTC enforcement area and are prohibited by Shopify's own guidelines
— and on a store whose whole model is repeat daily visits, they would erode the
trust the model depends on.

## The claimed bar is disclosed selectively, never adjusted

31 July. The bar now hides below 30% claimed and never shows a percentage at
all on an allocation under 10 units. Both numbers are theme settings, in Theme
settings → Deal urgency, shared by the homepage section and the PDP block so
the two cannot disagree.

**This is not a softening of "urgency is real, never synthetic" above — it is
the same rule enforced harder.** That decision bans fabricated countdowns and
invented percentages. Nothing here invents anything: the figure is still read
from inventory and is either shown exactly as it is or not shown. The choice
being made is whether a true number is worth saying, which is the same shape as
Shopify's own low-stock indicator, and the same shape as the upsell staying
silent on scaling suppliers.

Two things were wrong before.

**"3% claimed" at 9am undersells a deal that has all day to run.** It is true
and it argues against the product. On a store built on repeat daily visits the
bar's job is to report real movement, and reporting the absence of movement in
the first hour teaches people to come back later, which is the opposite of the
point.

**A percentage over a tiny allocation is precision the number cannot carry.**
One sale on a 3-unit deal is 33% — arithmetically true, and it tells a shopper
the deal is going three times faster than a single sale warrants. Those deals
now show "Only 3 left", which is the same fact with no implied rate.

Removed in the process: a `use_floor` / `floor_percent` pair that raised the
DISPLAYED percentage to a minimum of 15% when the real one was lower. It was
switched off and had never been on, but it was a setting that existed to print
a number the inventory did not support, one checkbox away from contradicting
the decision at the top of this file. Hiding a true number is a disclosure
choice; printing a false one is not, and the theme should not offer the second.

The consequence to accept: for the first part of most days the bar is absent,
so the space it occupies has to look deliberate. It renders nothing at all —
no wrapper, no empty track, no reserved height — because a container held open
for a bar that is not there reads as a broken page. A missing bar is expected
behaviour, not a bug.

## Deals never price below cost
`deal.py` reads each variant's unit cost from Shopify and clamps the deal price
to cost, then reports the discount actually applied rather than the one asked
for. Storefront Liquid cannot read cost, so this can only be enforced at setup.
Max discount before losing cash equals the supplier's margin: 50% for
prodigalpottery and Blessed Bayou, 40% for Gotta Go Gotta Throw, 30% for Shield
Your Body.

## Compare-at price must be a real former price
Never inflate compare-at above the normal price to manufacture a discount. The
correct shape is: compare-at holds the genuine regular price, price holds the
deal price. `deal.py` does this automatically, and also uses compare-at as the
restore slot — which is why a `price_snapshot` field exists as the authoritative
record, so enabling Collective's MSRP sync cannot confuse the revert.

## Never promise combined shipping
Every Collective supplier fulfils its own items, so a cart mixing suppliers
arrives as separate parcels on separate days. Any "ships together" claim is
false for most multi-item orders. The cart upsell prefers items from a supplier
already in the cart precisely because those genuinely do ship together — that
is the only context where the claim is true.

## Price bands are tag-based, not price-rule-based
Shopify's VARIANT_PRICE rule matches if ANY variant is in range, while the
product card shows the LOWEST price. Multi-packs therefore landed in the wrong
band and misrepresented themselves. `bands.py` computes the band from the
minimum variant price and writes a tag; collections match the tag.

## Cart gets a bespoke variant picker, everywhere else uses Horizon's quick-add
Only about 20% of the catalogue is single-variant, so a link-to-PDP upsell sent
most cart traffic away from the highest-intent page on the site. The cart picker
is purpose-built and updates the displayed price (variants are not uniformly
priced — one product runs $36 to $125). Everywhere else uses the theme's own
quick-add, because two add-to-cart patterns in one grid reads as a bug.

## The Meta token keeps ads_management, and the safeguard moves into code
Earlier this token deliberately excluded `ads_management`, on the reasoning that
a token which cannot spend money is one less thing to worry about. That has been
reversed: the ads agent will use this same token, and issuing a second one for it
would mean two credentials to rotate and two places to revoke.

**This changes where the safety lives, and it must not simply disappear.** The
old safeguard was structural — the credential physically could not spend. The
replacement has to be built, and it has to exist BEFORE anything calls a spend
endpoint, not after:

- a hard budget cap enforced in code before every call that can spend
- a spend ledger reconciled against what Meta reports, not against what we think
  we asked for
- daily budgets set at Meta itself, so the kill switch still works when the app
  is down or unreachable
- approval per campaign, not a single ENABLED boolean

Everything built so far is reversible: prices restore from snapshots, products
republish, posts delete. Ad spend is the first thing that leaves and does not
come back, so its guardrails differ in kind rather than degree. Until those
exist, no code path should call an ads endpoint at all.

## The deal ends, the product does not
A caption reading "Gone in 20 hours" says the item disappears. It does not — it
returns to full price and stays on the shelf. That is manufactured scarcity,
which this store already rules out for the countdown, and prose was quietly
reintroducing it.

It matters more than tone. The countdown is believed precisely because it counts
something real; a second, invented urgency beside it undoes the reason the first
one is trusted. The honest phrasing is also the better one: "Back to $279.00 in
20 hours" is concrete, read from the product, and makes the saving legible while
claiming nothing.

The same rule killed a teaser that promised "no extensions, no back by popular
demand" — a rule the store has deliberately engineered an exception to, in the
"Bring back this deal" button.

## Figures are composed, language is written
Deal captions used to be pure template, which made them truthful and made them
read like a spec sheet. They now carry a voice, under one constraint: every
NUMBER is still read from Shopify and formatted rather than typed, and every
hand-written line asserts nothing.

That is the whole arrangement. No line says "lowest price of the year" or
"selling fast" or "our best ever", because those are claims nobody can verify at
post time. Flavour cannot be false. It is what lets written copy sit in the same
caption as composed figures without reopening the hole composition closes.

Lines are keyed to discount depth — a shrug that suits 8% reads as sarcasm at
55% — and chosen by hashing the deal handle rather than at random, so the draft
previewed is the draft published.

## The vendor is never named in a post
On a dropship catalogue, naming the maker tells a shopper exactly who to go and
buy from directly. The same reason browsing is organised by category rather than
by supplier.

## Every agent lives in the app
Agents were spread across an embedded Shopify app, two GitHub Actions runners,
Fly secrets and a laptop terminal. Nothing could answer "is everything running?",
each new agent added another place to look, and half of it needed a CLI — which
in practice meant one person, from one machine.

They now all run in the app, report to one page, and are switched on and off with
buttons whose state lives in Shopify rather than in environment variables. The
test is not elegance, it is whether Jake can operate it.

GitHub Actions was also actively wrong for this: it disables scheduled workflows
after 60 days of repository inactivity, so the jobs would have stopped precisely
during a quiet period, which is when nobody is watching.

## An invariant checker, not an orchestrator
Every agent here is individually careful and the failures still fall between
them: a forced rotation once left forty products discounted and unowned, with
each agent behaving exactly as written.

The fix is a linter, not a manager. It asserts flat statements that are true or
false, changes nothing, and cannot reason its way around a rule. A supervising
agent would have caught none of the failures actually seen — they were a missing
scope, a syntax error, a race and a bundler split — while making each one harder
to diagnose, because the first question becomes "what did the supervisor decide?"

Revisit when agents genuinely compete for a scarce resource. Ads will create
that, and even then it should propose rather than decide.

## Attribution is measured, or it is labelled a comparison
Engagement is measured: likes, comments and reach come from Meta and are facts.

Sales are not attributed, because nothing available can honestly attribute them —
an Instagram caption has no click-through. What is shown instead is a before and
after inside the same deal window: same product, same discount, same day, split
at the moment the post went out. The page states plainly that it does not control
for time of day.

A figure labelled attribution that is really correlation is worse than no figure,
because it gets believed and then budgeted against. Links now carry UTMs so this
becomes a real measurement rather than an inference.

## The Bargain Bin is separate machinery from the Yoink
They answer different questions. The Yoink asks what single thing to discount
hardest today; the bin asks what forty things can be held at 25% off for a week
without losing money. Folding the second into the first would have meant one
selector serving two incompatible objectives, and the bin's weekly restore-and-
reprice sitting in front of the job that changes the day's price.

So: separate module, metaobject type, cron endpoint, heartbeat and scheduler
tick. They share `pricing.server.ts` for the price writes, because that is where
the never-below-cost floor lives and there must be exactly one of those.

The coupling is deliberately two filters and no more. **A product can be in only
one discount state at a time**: the bin refuses anything live or queued inside
the deal horizon, and the deal candidate pool refuses anything already in the
bin. Without both, each system holds a restore snapshot for the same product and
whichever restores second writes the other's discounted price back as the
regular one. That failure is silent, and it compounds every cycle.

## Bin selection interleaves by vendor rather than ranking by margin
Ranked purely by margin this catalogue returns a bin that is two vendors and 90%
one maker, because a single supplier is 54% of the eligible pool. Round-robin
across vendors, best margin first within each, returns all twelve with the
largest at 10%.

This is the same lesson the deal candidate pool learned when ranking by discount
collapsed eighteen suppliers to three. A bin that is mostly one maker is a shelf,
not a bin — and on a dropship catalogue it also tells a shopper exactly which
supplier to go buy from directly.

## Sold-out products are unpublished, not tagged
The ask was that they not show up. A tag plus a collection rule hides a product
from the price bands and the category collections and nothing else — it stays in
search results, in `/collections/all` which the homepage cross-sell reads, and in
the sitemap. Unpublishing is the only thing that means what it says.

The cost is Google index churn, which is why it debounces: two consecutive
zero-stock readings before acting, because Collective's inventory sync blips to
zero between a supplier's push and its confirmation, and a product flickering in
and out of the sitemap every thirty minutes is worse than one that is briefly
visible and sold out.

The live deal and anything queued within seven days is exempt. A sold-out Yoink
is *supposed* to be visible — the countdown and the claimed bar are the point,
and hiding it would 404 the announcement bar, the Meta post and every share.
Worse, activation looks a product up by id and would happily reprice an
unpublished one: priced, counting down, invisible.

State rides on tags rather than a table so there is nothing new to persist, and
the `oos` tag doubles as the permission slip for republishing — a product taken
down by hand carries no tag, so the sweep never resurrects it.

## Meta posting is autonomous once it is switched on
The original brief called for a human to approve every post. We kept the
scheduled job posting unattended instead, because there is nothing for a human to
review: captions are composed from Shopify facts by template, not written by a
model, so the truth guarantee is structural rather than a matter of the caption
behaving. The one real risk — posting the wrong product because two deals were
live at once — is now a hard refusal in the script.

What a human would actually be approving is the brand voice, and that is a
property of the template, which is reviewed once rather than daily.

## The deal hero follows the variant picker
The Yoink is often one form in nine glazes, so the colour a shopper picks *is*
the decision, and a static photo answers a different question. The page used to
open on a mismatch — one file showing while the dropdown named another colour.

Supplier photography is uneven: of those nine colours four have no photo of their
own and two share one. So every lookup falls back to the product image rather
than blanking the hero. A picker that swaps to nothing is worse than one that
does not swap at all.

## Category titles are overridden, handles are not
Shopify's standard taxonomy names segments for completeness, not for shop
windows: "Food, Beverages & Tobacco" is the real top-level segment even when
nothing in the collection is tobacco, and that word does not belong on the
homepage. `categories.py` carries a `DISPLAY_NAMES` map and applies it to
existing collections as well as new ones.

Only the shopper-facing title is overridden. The tag and the handle still follow
the taxonomy, because the collection rule matches `tag == handle` — renaming the
handle would mean retagging every product in it. The consequence is that the URL
can disagree with the title, which is the cheaper of the two problems.

## Category navigation is deliberately deferred
Supplier categories arrive from Collective as whatever each supplier called
them, so most of the catalogue was typed "Ceramic" and some had no type at all.
Building a category tree against a catalogue that is 89% one vendor would bake
in that skew. Price bands work today and survive any catalogue mix. Revisit once
there is enough variety that the real categories are obvious.

## Nothing is final sale

30 July. Shoppers assume a 45%-off item is non-returnable, so saying otherwise
is the strongest trust signal a store with no review history can offer — and it
costs nothing until someone actually returns something. The final-sale line was
removed from the draft policy entirely rather than left dormant: "items marked
final sale" invites a shopper to wonder which ones are, and the answer is none.

## The customer-facing return window ignores vendor terms

30 July. ~40 Collective vendors have widely varying return windows and there is
no number that sits inside all of them. That is the wrong thing to optimise: The
Yoink is the merchant of record, so vendor terms decide how much we *recover*,
not what we *owe*. 14 days, chosen for conversion and for being sayable from
memory, with recovery treated as a cost line and triaged case by case.

## Defects keep a 30-day window while everything else tightens

30 July. Every other clause got stingier; this one deliberately did not.
Narrowing it does not reduce exposure, it converts it into chargebacks — which
cost the money, the goods, a dispute fee, and count against the ratio that gets
a payments account reviewed. Implied warranty of merchantability is also not
waivable in a fair number of states.

## The prompt version belongs in the cache key

30 July. Enrichment skipped products whose source fields were unchanged, which
meant improving the prompt could never improve the catalogue. The prompt is an
input to the answer exactly as the description is. Re-reading the whole
catalogue costs a few dollars; a permanently frozen catalogue costs the feature.

## Curation signal is split between tags and typed metafields

30 July. Occasions, recipients and settings stay as `e-` tags — they already
drive automated collections and Search & Discovery. `hero_score` and `color`
became definition-backed metafields, because a JSON blob reaches the Storefront
API as an opaque string and neither the chatbot nor Search & Discovery could
ever have read it. Typed also means sortable, which a tag cannot express: there
is no tag for "score >= 4".

## The Yoink gets a tag and a collection, reconciled not evented

30 July. A metaobject is reachable from Liquid and the Admin API and almost
nothing else, so every external consumer was blind to which product is on deal.
The tag is written by reconciling the tagged set against live deals on each run,
rather than tagging on activate and clearing on sweep — two writers drift the
first time a deal window is edited by hand, and a reconciler self-heals.

## Deal windows are anchored to store time

30 July. Anchoring to UTC made the rollover correct in July and wrong from
November, with no error and nothing to notice it. The deal time is a
shopper-facing promise, so it belongs on the shopper's clock.

## US only, for now

30 July. Canada and International delivery zones were deleted. International
returns on a dropship catalogue are a money pit, and the returns process is not
settled enough domestically to extend it across a border.

## Shipping stays pass-through, not flat

31 July. A flat $6.95 was the recommendation until the vendor data existed, and
the data reversed it. Three reasons, in order of weight.

It would kill the best lever: 56% of products belong to a supplier with a
REACHABLE free-shipping threshold. Under a flat rate, "add $18 more from this
brand and shipping is free" becomes false — their shipping does not change — so
we would pocket the supplier's threshold discount silently instead of spending
it as a customer incentive. The incentive is worth more.

It cannot be tiered. Delivery-method conditions support weight and price, not
vendor, and Collective products ship from supplier locations so a separate
profile does not work at all. Flat means ONE rate for everything, and the 22% of
products from oversize suppliers would bleed $4.65 an order.

And pass-through never loses money. On a store with $12.67 median contribution
and no sales history, "shipping is exactly cost, always" is worth a lot.

The cost of this decision is real and accepted: shipping stays variable, and
deal-hunters do notice. If traffic later shows it suppressing conversion, the
answer is a store-wide free-shipping threshold on top — additive, giving nothing
up — not a flat rate.

## Shipping is a conversion input, not a cost input

31 July. Because it passes through at zero markup, shipping does not touch
margin. It decides whether the OFFER survives: $9.99 off with $13 shipping is a
$23 purchase dressed as a $10 one, and four suppliers ship for more than their
item is worth. So it enters the Yoink ranking and the Bargain Bin filter as a
35%-of-price cap, and enters nothing as a cost adjustment.

## A shipping claim is measured per product, never inferred per vendor

31 July. Vendor shape predicts well and does not guarantee: Fuse Audio ships six
of seven products free and charges $12 on a heavy radio. A badge is a promise to
a shopper, so a measured per-product cost overrules the brand's shape in BOTH
directions — a measured non-zero cost mutes "free" rather than being overridden
by it. Verified against all 181 free-vendor products: 179 genuinely free, 99%.

## The upsell stays silent on a third of suppliers

31 July. Nine suppliers get more expensive as items are added, and six have a
threshold their own catalogue cannot reach. Both render nothing. Inviting a
bigger basket from a scaling supplier costs money, and quoting a gap nobody can
close is a promise with nothing behind it. Silence is a correct answer and the
common one.

## Long agent work is budgeted in time, not in units

31 July. The shipping agent's probes are ~2.3s each because every one is a live
callout to Collective. A 300-probe budget needed 23 minutes and was killed by
the request timeout on every run, writing nothing. Wall-clock budgets always fit
the timeout and degrade to fewer probes rather than to failure. Any future agent
that calls a third party should do the same.

## Nothing is final sale, and defects keep 30 days

31 July, published. Every other clause tightened — 14 days, customer pays return
shipping — and this one deliberately did not. Narrowing the defect path does not
reduce exposure, it converts refunds into chargebacks, which cost the money, the
goods, a dispute fee, and count against the ratio that gets a payments account
reviewed. Shoppers assume deep discounts are non-returnable, so saying otherwise
is the strongest trust signal a store with no reviews can offer.

## The chatbot may name suppliers

31 July. The guardrail relaxes from "never name a brand" to "do not lead with
it". The storefront already names suppliers in the cart, on the PDP, and in 48
browsable vendor collections, so silence prevents nothing and reads as evasive
next to a page that names the brand. The upsell copy stays brand-free anyway —
"ships with what's already in your cart" is the better reason regardless, because
the shipping relationship is the persuasive part and the brand is incidental.

## Categories are filled from productType, not from the vendor's mode

31 July. 143 published products had no Shopify taxonomy category, so they were
absent from Shop by Category and reachable only by search. Filling each from its
vendor's most common category is the obvious move and would have been wrong:
Sweet Bamboo's mode covers 23% of its catalogue and prodigalpottery's 21%, so
the mode is a minority opinion. `productType` — "Vacation Slides", "Footies",
"Ceramic" — describes the actual product and was accurate across all 39
vendor/type groups. Where a vendor already had categorised products, their exact
taxonomy ids were reused rather than resolved by search, because an id that
vendor is already using cannot be wrong.

## A product that cannot be shipped gets unpublished, not deleted

31 July. 22 published, in-stock products from one supplier returned no shipping
rate, so checkout dead-ended on them. Unpublished rather than deleted: they are
Collective products, so deleting would only resync them, and the fault is the
supplier's rate configuration rather than anything about the product. Each is
tagged `no-ship-rate` so the set is findable and the action reversible in one
command, following the same convention as `oos`.

## The 21% with punishing shipping stay listed

31 July. 281 products cost more than 35% of their price to ship. They are
excluded from Yoink candidates and the Bargain Bin automatically, so they cannot
embarrass a deal surface, but they remain listed and buyable. They are not
broken — they sell, they just look poor value — and with no traffic there is
nothing to be gained by culling a fifth of the catalogue on a judgement call.
Revisit with real order data.

## Category rules are learned from the catalogue, not written down

31 July. Filling a missing category needs a mapping from something the product
does have — vendor and productType — to a taxonomy id. That mapping could be a
table in the repo, and it would rot: suppliers arrive, product types change, and
nobody would remember to edit it.

Instead the rules are derived from the live catalogue: every vendor+productType
combination where at least two categorised products agree on a category becomes
a rule. That makes the fill a propagation of a decision already made rather than
a guess, and it self-updates as the catalogue changes. Seventy-three rules came
out of a catalogue where I had hand-mapped thirty-nine.

Two agreeing examples is the threshold on purpose. One product is an anecdote,
and a rule built from an anecdote would confidently miscategorise everything
that followed it.

## Unbuyable is unbuyable — no shipping rate hides a product, on the second reading

31 July. Twenty-two published, in-stock products returned no shipping rate and
dead-ended at checkout. That is the same customer outcome as out of stock, so it
gets the same treatment and the same shape: a pending tag on the first reading, a
settled tag and an unpublish on the second, and the settled tag doubling as the
permission slip to republish.

The debounce is not decoration. Carrier services fail transiently, and hiding a
product on one bad answer would make the storefront flicker — the same reasoning
that put a two-reading rule on the sold-out sweep.

Products that set `requiresShipping: false` are exempt. The first run of this
unpublished a gift card. "Nothing will ship it" is only a fault when the thing is
meant to be shipped, and a rule that cannot tell the difference is worse than no
rule.

