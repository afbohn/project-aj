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

**SUPERSEDED 1 August — the bar itself is gone.** See "Momentum, not scarcity"
below: the allocation turned out never to have been enforced, which made "Only 3
left" false rather than merely coarse. The disclosure principle here survived
intact and is what the sold count's threshold is built on; only the figure being
disclosed changed. Kept because the reasoning is still the reasoning.

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

## Automatic refunds are off, and that makes refunds our job

31 July. Collective's default processes the refund itself when a return closes.
That is less work and it forecloses the entire store-credit workstream — there
is no moment at which "refund cash, or keep it and issue credit at 110%?" can
be asked, because the cash has already gone.

Turned off deliberately, accepting the operational cost: **an accepted return
now refunds only if something we built does it.** This trades a silent
correct-by-default behaviour for a loud one that can break, which is the right
trade only if the handler actually gets built. Until `returns/close` is
listening, refunding is a manual step and the risk is a customer who returned
an item and hears nothing.

The prize is that credit costs COGS rather than face value — a $50 credit
against a 50%-margin item costs ~$25 — so 110–115% in credit reads as more
generous than 100% in cash and costs less. Do not model around unredeemed
credit; the point is the margin difference, not breakage.

## The catalogue is much thinner than the four documented suppliers suggest

31 July, measured against real `unitCost` on 10,593 costed variants rather than
the four suppliers this file has been quoting.

Those four are exact — prodigalpottery 50%, Gotta Go Gotta Throw 40%, Shield
Your Body 30%. They are also not representative. The catalogue median is 40%,
**34.7% of variants sit below 30%**, and the floor is far lower than the 30%
this file has been treating as worst case: Miller Bison and Bear Dice at 10%,
Intelligent Change and Elijah's Xtreme at 15%, and Wags & Whiskers — 189
variants — at 16%.

Two consequences.

**A 10%-margin product cannot carry a Yoink.** After 2.9% + $0.30 its
break-even discount is around 5%, which is not a headline. Those suppliers are
browsable catalogue, not deal candidates, and the selector should say so rather
than discovering it per-product.

**Six ACTIVE variants are priced BELOW cost right now**, all Wags & Whiskers,
worst at $58.99 against a $62.15 cost. They lose money at full price with no
discount involved, so no margin floor catches them — every floor here is
expressed as a discount off a price that is already wrong.

## Keeping the item and taking store credit are two separate offers

31 July, late. The returns logic was run over real deal values for the first
time and got the case this store cares most about wrong: a $5.66 DEFECTIVE
return came back as keep-it-and-credit — no cash, $6.23 in store credit.

The keep-it arithmetic is right. Below roughly $25, return postage plus
handling exceeds what the item recovers, and recovery is not even certain
because ~40 suppliers have ~40 different terms. Asking for a cheap item back is
worse than letting it go.

**But that is an argument about the ITEM, and it was being used to decide the
MONEY.** The published refund policy says of anything damaged, defective or
wrong: *"We'll replace it or refund it in full, including shipping."* Answering
that with a voucher contradicts a page the customer can open in another tab —
on the one clause this file has most deliberately kept generous. The 30-day
defect window exists because narrowing the defect path does not reduce exposure,
it converts refunds into chargebacks; offering credit for a broken item is the
most reliable way to produce one. A few dollars of margin against a dispute fee,
the goods, and the ratio that gets a payments account reviewed.

So a fault under the line is **keep it AND refund cash**: they keep it, because
posting a broken thing back helps nobody, and the money goes back as money.
Change-of-mind under the line still gets credit at 110%, which is a genuinely
better offer there and costs less because credit is costed at COGS.

The general form, worth keeping: **a cost argument may decide logistics and
must not decide an obligation.**

## The Yoink rolls over at midnight, because the boundary is the decision

1 August. A 24-hour window contains one of every hour, so the only real choice
is which hours get the countdown's final and most persuasive stretch. At 9am
Central the last hours ran 6-9am — the deadest window in the country — so the
clock did its best work in front of nobody, and a West Coast shopper who slept
on a deal found it gone before waking.

Midnight Central puts the closing hours at 9pm-midnight Eastern and 6-10pm
Pacific, prime time on both coasts, and leaves a fresh deal waiting when
everyone wakes up. It also moves the sold count's hidden stretch — below ten,
where it renders nothing — out of the morning and into the small hours. Woot and
Meh both roll overnight, for the same reason.

The cost is that activation is now unattended, and that is only affordable
because the 8am digest catches a failed rollover before the day's traffic. The
ordering matters: the digest had to exist first.

## Momentum, not scarcity — count what sold, never what is left

1 August. "Only 12 left" and the % claimed bar both rested on `units_allocated`
being a limit we would honour. It never was — nothing caps sales at the
allocation — and the decision is that nothing should: **if a supplier has stock,
we want to sell it.**

That makes the scarcity line false at the moment it prints, on a product whose
supplier holds fourteen thousand units. It is the manufactured urgency this file
rules out at the top, arrived at by accident rather than intent, which is the
only way it could have survived this long.

So the claim goes and the count stays. Two urgencies remain and both are real:
**time**, via a countdown against an absolute timestamp, and **momentum**, via
units that genuinely sold. Momentum cannot become a lie however much we sell,
which is exactly why it survives a decision to sell everything available. A
percentage cannot — it needs a denominator, and the only one available is a
number we have decided not to enforce.

The display threshold survives in its new form: "3 yoinked today" argues against
the deal exactly as "3% claimed" did, so nothing renders below ten.

## The teaser may evoke a person; it may never identify the product

1 August. The sneak peek shows a hint about tomorrow's Yoink, written per
product by the enrichment agent. One rule governs it, and it is the rule that
already keeps vendors out of social posts: **a Collective SKU is not exclusive**,
so naming tomorrow's item gives a day's head start to anyone who wants to
price-compare it.

So the hint evokes a person or a moment and never the object — no category,
brand, material, colour, price or discount. "For whoever still keeps the good
dice in a velvet bag", not "a D&D book". An empty string is an explicitly good
answer, and the block reads fine without one, which is why the hint is last
rather than load-bearing.

It is also the only line the enrichment agent writes FOR A SHOPPER rather than
for a colleague — everything else it produces is curation signal read by
machines. The same constraint that governs deal captions applies: flavour cannot
be false.

## The product page is ordered by what each block argues

1 August. The full description sat between the price and the variant picker,
pushing add-to-cart down on every product — median description is 645
characters, p90 is 1,605, and the longest is 11,836.

The ordering rule is not "important things first", it is **everything that
argues for the sale goes above the button, everything else below**: title,
price, supplier shipping, countdown, sold count, variants, buy. Then ships-from,
then the description, then the sneak peek last — so a shopper who has not bought
gets the full description before being offered tomorrow.

That rule also forced a split. `aj-deal-urgency` bundled the countdown with the
sneak peek, and those argue opposite things: one that you should buy now, one
that there is another chance tomorrow. While they shared a block the page could
only ever put one of them in the right place, and the editor had reasonably
placed the pair above the button — which put the argument against buying at the
moment of highest intent.

## A number only gets stated when it helps

1 August. Two instances of the same rule, worth naming once.

The sneak peek said "priced over $50", which on a store whose whole promise is a
bargain reads as a warning rather than a hook. The pull is asymmetric — "under
$10" is a reason to come back and "over $50" is a reason not to — so the copy is
asymmetric too: the cheap bands are stated, the expensive ones are not mentioned
and the category carries the line alone.

Same shape as the sold count's threshold, and the same distinction throughout:
**this is omission, never adjustment.** Nothing claims tomorrow is cheap; a
figure that does not help is simply not the thing we lead with. Adjusting a real
number to look better is the line, and it is not crossed here.

## Shipping is emphasised by what the line is doing, and free shipping is not a badge

1 August. Emphasis was inverted. "Free shipping" rendered at 0.85 opacity and
"Add $44.00 more from this brand" rendered at weight 600 — shouting the ask and
whispering the gift. Three tones now, decided in the snippet rather than by
whoever places the block: **free is a pill, a line that names a cost is plain
body text, and the nudge is plain and cart-only.**

The nudge had to move regardless. It reads `cart_vendor_total`, no caller has
ever passed one, so `spent` was always 0 and every threshold supplier printed
"Add $44.00 more" on the PDP to a shopper with an empty cart who had not yet
added the item in front of them. Absent is now distinguished from zero: with
cart context it asks for the gap, without it states the same fact as a fact.

**On cards the mark is not a badge, and that is the decision.** The badge slot
holds exactly one thing and that thing is the size of the discount, which is
what stops the scroll on a store built around a bargain — a second badge there
either displaces it or crowds it, and "Ships free" loses that contest against
"40% off" every time. It sits with the price instead, which is also where it is
most useful: free shipping is arithmetic, not a hook, and the shopper doing the
sum is looking at the number.

The cost, stated so it stays a choice: 279 of 1,472 published products ship
free, so marking 19% of cards makes the other 81% implicitly read as "shipping
extra". That is true, and it moves the discovery from checkout — where it causes
abandonment — to browsing, where it informs a choice. Same trade as naming the
supplier on the product page.

**A shipping number is stated as "from", never as a price.** `ship.cost` is a
real `draftOrderCalculate` quote, so it is what a customer pays rather than what
the supplier charges us — but it is measured to one destination, at quantity 1,
taking the cheapest rate. "From" is honest in all three directions and errs
toward overstating the cost, which is the safe direction for a claim and the
same reasoning that keeps a delivery date off `aj-ships-from`.

## The API budget is a library, not a supervisor

31 July, late. Two agents started returning `Throttled` in the same minute.
Shopify's GraphQL limit is a leaky bucket per app per shop, so all eight agents
draw from one balance — which makes it the first genuinely scarce shared
resource here, and the exact condition "an invariant checker, not an
orchestrator" named as the trigger to revisit itself.

Revisited, and the answer is unchanged. A supervisor cannot make a query
cheaper or refill the bucket, and it would add a second thing to diagnose when
a run fails — "what did the supervisor decide?" — which is the original
objection. What the bucket needs is for callers to WAIT when it is empty, and
Shopify states in every response how many points remain and how fast they
refill, so the wait is arithmetic rather than negotiation. That belongs in the
client, wrapped once where the admin client is created so no job can forget it.

Capped at four attempts and ten seconds. A job that sleeps longer than its own
budget is killed by the request timeout having written nothing, which is the
failure the shipping agent already paid for once. Give up, report, let the next
tick make progress.

## Shopify bills the connection size you ASK for

31 July, late, and this is why the bucket was empty. Every full-catalogue sweep
requested `variants(first: 100)` on all 1,503 products. Measured, the catalogue
is p50 **3** variants, p75 7, p90 16, p95 24, p99 85 — so the median product was
billed for a hundred and used three, in three separate agents, every half hour.

A smaller number alone would have been the wrong fix, because it truncates, and
truncation is the thing this repo has paid for repeatedly. So each sweep asks
for 25 AND asks `variantsCount` how many there really are, then tops up the few
that exceed it. Roughly 47 extra small calls against a 4x cut on every page.

It is also more correct than what it replaced: `first: 100` truncated silently
AT 100, with no way to detect it, and one product sits on exactly 100 variants
today. The margin floor is measured on the WORST variant, so a short list there
is not merely incomplete — it is optimistic, in the direction that loses money.

**The next lever is Bulk Operations, and the trigger is growth.** Cheaper pages
scale with variants; page COUNT scales with the catalogue. Bulk is the only
option indifferent to catalogue size. Do it when any of these fire: `Throttled`
returns despite the backoff, the catalogue sweep's "variant lists completed"
climbs past ~150, or a sweep's duration approaches the request timeout. Note it
allows one operation at a time per app per shop, so three sweeps wanting it is
the one place a lock is genuinely warranted.

## The brand palette, measured

31 July. Sampled from `Logo-Test-2.png` rather than chosen: purple `#814a9e`,
yellow `#ffde00`, cyan `#43afca`. Against white:

| | ratio | verdict |
|---|---|---|
| purple | 6.16:1 | passes as text |
| yellow | **1.34:1** | fails as text AND as a 3:1 UI border |
| cyan | **2.55:1** | fails as text AND as a 3:1 UI border |

So **purple carries every word**, and yellow and cyan may only ever be
BACKGROUNDS with dark text on them — ink on yellow is 12.65:1, ink on cyan
6.62:1. Yellow cannot even be a hairline rule against white, which is why it
appears in the digest email as a chunky band: decoration carries no information
and therefore has no contrast requirement.

This is the "yellow on white will fail" case the brief predicted, now confirmed
by measurement. It will be tempting when the real brand work starts, because
yellow is the most energetic colour in the mark and the obvious thing to set
type in. It cannot be used that way on white at any size.

**Status colours stay separate from brand colours.** Red, amber and green in
the digest are information; repainting them on-brand would put "yellow means
late" beside "yellow means The Yoink". Every row also keeps its word, so state
never rides on colour alone.

## We do not sell shipping protection

31 July. The checkbox every deal site runs — a few dollars to insure the parcel
— is tempting on a store whose orders net $2–3, because the fee is pure margin
and would roughly double that.

**We already promise it for free, in writing.** The refund policy says transit
damage inside 48 hours is replaced or refunded in full including shipping, with
the return paid. So a protection fee has exactly two shapes and both are bad:
it duplicates a promise a customer can disprove by reading our own policy page,
or we narrow the policy to make room for it — and narrowing the damage path is
already refused above, because it converts refunds into chargebacks.

Three more, in order of weight. Selling *insurance* without a licence is
regulated state by state, and the apps in this space have been sued over
precisely that framing. These offers are almost always pre-checked opt-outs,
which is a negative-option dark pattern and the same family as the fabricated
countdowns and invented "% claimed" bars this store already rules out — on a
model built from repeat daily visits, that trust is the asset. And with no
orders there is no claim rate to price against, on parcels packed in someone
else's warehouse.

The inverse is the better trade and costs nothing until someone claims: say the
cover is free and included, which is differentiated AGAINST every site running
the checkbox. Identical reasoning to "nothing is final sale". The margin we
actually wanted comes from merch at ~68%, not from a fee that spends trust.

Note that a **Shipping Protection product does exist in the catalogue** — it is
vendor Navigate Craft's own UpCart SKU, synced in through Collective, and it is
unpublished. Not ours, and not a decision. See state.md.

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

