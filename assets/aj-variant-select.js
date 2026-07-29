/**
 * <aj-variant-select> — a compact variant picker for the cart upsell.
 *
 * Deliberately thin. Horizon's `product-form-component` already does the hard
 * part: it intercepts the form submit, posts to the cart, asks for the cart
 * sections back, and morphs them into place so the drawer updates without a
 * reload. It reads the variant from the hidden input marked `ref="variantId"`.
 *
 * So all this does is keep that hidden input in step with the <select>, and
 * keep the visible price honest. Everything else is the theme's.
 *
 * The price matters more than it looks. Variants on this catalogue are not
 * uniformly priced — "Artisan Soup Mugs" runs $36 for one to $125 for a set of
 * four — so a picker that changes the variant without changing the price shows
 * someone $36 and charges them $125. Each option carries its own formatted
 * price, rendered server-side, and the display follows the selection.
 */

class AjVariantSelect extends HTMLElement {
  connectedCallback() {
    this.select = this.querySelector('select');
    // The hidden input lives in the sibling form, not inside this element, so
    // scope the lookup to the shared row rather than to `this`.
    this.row = this.closest('[data-aj-upsell-row]') || this.parentElement;
    this.variantInput = this.row?.querySelector('[ref="variantId"]');
    this.priceEl = this.row?.querySelector('[data-aj-upsell-price]');
    this.button = this.row?.querySelector('button[type="submit"]');

    if (!this.select || !this.variantInput) return;

    this.select.addEventListener('change', () => this.sync());
    // Sync once on connect: a browser restoring a previous selection on
    // back-navigation would otherwise leave the hidden input on the default.
    this.sync();
  }

  sync() {
    const option = this.select.selectedOptions[0];
    if (!option) return;

    this.variantInput.value = option.value;

    const available = option.dataset.available === 'true';
    this.variantInput.disabled = !available;
    if (this.button) {
      this.button.disabled = !available;
    }

    if (this.priceEl && option.dataset.price) {
      this.priceEl.textContent = option.dataset.price;
    }
  }
}

if (!customElements.get('aj-variant-select')) {
  customElements.define('aj-variant-select', AjVariantSelect);
}
