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

## Category navigation is deliberately deferred
Supplier categories arrive from Collective as whatever each supplier called
them, so most of the catalogue was typed "Ceramic" and some had no type at all.
Building a category tree against a catalogue that is 89% one vendor would bake
in that skew. Price bands work today and survive any catalogue mix. Revisit once
there is enough variety that the real categories are obvious.
