/**
 * <aj-email-popup> — the capture modal.
 *
 * THE INTERESTING PART IS ALL THE TIMES IT DOES NOT OPEN. A popup that appears
 * on every page load to everyone is the version people install ad blockers for,
 * so the suppression rules matter more than the presentation:
 *
 *   - never on the join page (they are already looking at the form)
 *   - never after a signup, permanently — asking again after someone said yes
 *     is the fastest way to make them regret it
 *   - never inside the dismissal window
 *   - never before the delay, so the Yoink is what a visitor sees first
 *
 * State lives in localStorage, which means it is per-device and a shopper on a
 * new phone will be asked again. That is the correct trade: the alternative is
 * identifying people before they have given us anything, and the cost of the
 * occasional repeat ask is much lower than the cost of that.
 *
 * SUBMISSION IS LEFT TO SHOPIFY. The form posts and the page reloads with
 * `?customer_posted=true`, which is how the theme's own forms work — no fetch,
 * no JSON endpoint, nothing to keep in step with Shopify's form handling. The
 * only thing this script does on the way out is record the signup so the popup
 * never returns.
 */

const SEEN_KEY = "aj_pop_dismissed_until";
const JOINED_KEY = "aj_pop_joined";

/**
 * Set on THIS form's submit, read after the reload, then cleared.
 *
 * Every signup on the store returns to `?customer_posted=true` — footer, join
 * page and the deal panel all use the same Shopify form. The deal panel's people
 * get tomorrow's preview and no discount code, so the success copy here would be
 * false for them. This marker is the only thing that survives the round trip and
 * says the popup itself was the form that was used.
 */
const FROM_POPUP_KEY = "aj_pop_submitted";

class AjEmailPopup extends HTMLElement {
  connectedCallback() {
    this.panel = this.querySelector(".aj-pop__panel");
    this.form = this.querySelector("form");

    // Shopify redirects back with this after a successful post. Record it before
    // any open check runs, so a signup made through the popup also suppresses
    // the footer-driven one on the next page.
    if (location.search.includes("customer_posted=true")) {
      this.remember(JOINED_KEY, "1");
      let mine = false;
      try {
        mine = localStorage.getItem(FROM_POPUP_KEY) === "1";
        localStorage.removeItem(FROM_POPUP_KEY);
      } catch { /* storage disabled: fall through and stay shut, as before */ }
      if (mine) this.confirm();
      return;
    }

    if (!this.shouldOffer()) return;

    for (const el of this.querySelectorAll("[data-close]")) {
      el.addEventListener("click", () => this.dismiss());
    }
    this.onKey = (e) => { if (e.key === "Escape") this.dismiss(); };

    // A submit is consent to be asked never again, whether or not the round trip
    // succeeds — a validation error should not resurrect the popup later.
    this.form?.addEventListener("submit", () => {
      this.remember(JOINED_KEY, "1");
      this.remember(FROM_POPUP_KEY, "1");
    });

    const delay = Number(this.dataset.delay || 12) * 1000;
    this.timer = setTimeout(() => this.open(), delay);

    // Desktop only: a phone has no cursor to leave the viewport with, so exit
    // intent there would mean the popup effectively never fires.
    if (this.dataset.exitIntent === "true" && window.matchMedia("(hover: hover)").matches) {
      this.onLeave = (e) => { if (e.clientY <= 0) this.open(); };
      document.addEventListener("mouseout", this.onLeave);
    }
  }

  shouldOffer() {
    // Asking someone to subscribe on the page whose entire purpose is
    // subscribing is the worst version of this pattern.
    if (/\/pages\/join\b/.test(location.pathname)) return false;
    if (/\/(checkouts?|cart|account)\b/.test(location.pathname)) return false;
    try {
      if (localStorage.getItem(JOINED_KEY)) return false;
      const until = Number(localStorage.getItem(SEEN_KEY) || 0);
      if (until && Date.now() < until) return false;
    } catch {
      // Private mode or storage disabled: without a memory we cannot promise
      // "only once", and a popup that cannot keep that promise is worse than
      // none. Stay shut.
      return false;
    }
    return true;
  }

  /**
   * Reopen on the success state after the round trip.
   *
   * SCROLLING TO THE TOP IS THE POINT, not a flourish. Shopify's form posts to
   * `#contact_form`, so the browser lands you at the FOOTER — which is why a
   * popup signup used to dump people at the bottom of the homepage looking at a
   * menu. The anchor is also stripped from the URL so a refresh does not repeat
   * the jump.
   */
  confirm() {
    const done = this.querySelector('[data-state="success"]');
    const form = this.querySelector('[data-state="form"]');
    // No success block means an older theme copy is live; the old silent
    // behaviour is the correct fallback, never a half-rendered dialog.
    if (!done) return;

    if (form) form.hidden = true;
    done.hidden = false;
    this.panel?.setAttribute("aria-labelledby", "aj-pop-done");
    this.hidden = false;
    this.opened = true;

    try {
      history.replaceState(null, "", location.pathname);
    } catch { /* a stale URL is cosmetic */ }
    window.scrollTo({ top: 0, behavior: "auto" });

    this.onKey = (e) => { if (e.key === "Escape") this.close(); };
    document.addEventListener("keydown", this.onKey);
    for (const el of this.querySelectorAll("[data-close]")) {
      el.addEventListener("click", () => this.close());
    }
  }

  /** Shut without writing a dismissal window — they joined, not declined. */
  close() {
    this.hidden = true;
    document.removeEventListener("keydown", this.onKey);
  }

  open() {
    if (this.opened) return;
    this.opened = true;
    clearTimeout(this.timer);
    this.hidden = false;
    document.addEventListener("keydown", this.onKey);
    // Focus the input, not the panel: the next thing anyone does here is type.
    this.querySelector(".aj-pop__input")?.focus({ preventScroll: true });
  }

  dismiss() {
    const days = Number(this.dataset.rememberDays || 30);
    this.remember(SEEN_KEY, String(Date.now() + days * 86400000));
    this.hidden = true;
    clearTimeout(this.timer);
    document.removeEventListener("keydown", this.onKey);
    if (this.onLeave) document.removeEventListener("mouseout", this.onLeave);
  }

  remember(key, value) {
    try { localStorage.setItem(key, value); } catch { /* nothing to do */ }
  }
}

if (!customElements.get("aj-email-popup")) {
  customElements.define("aj-email-popup", AjEmailPopup);
}
