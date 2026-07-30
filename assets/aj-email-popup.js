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

class AjEmailPopup extends HTMLElement {
  connectedCallback() {
    this.panel = this.querySelector(".aj-pop__panel");
    this.form = this.querySelector("form");

    // Shopify redirects back with this after a successful post. Record it before
    // any open check runs, so a signup made through the popup also suppresses
    // the footer-driven one on the next page.
    if (location.search.includes("customer_posted=true")) {
      this.remember(JOINED_KEY, "1");
      return;
    }

    if (!this.shouldOffer()) return;

    for (const el of this.querySelectorAll("[data-close]")) {
      el.addEventListener("click", () => this.dismiss());
    }
    this.onKey = (e) => { if (e.key === "Escape") this.dismiss(); };

    // A submit is consent to be asked never again, whether or not the round trip
    // succeeds — a validation error should not resurrect the popup later.
    this.form?.addEventListener("submit", () => this.remember(JOINED_KEY, "1"));

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
