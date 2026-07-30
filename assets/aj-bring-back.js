/**
 * <aj-bring-back> — "bring this back" on a finished Yoink.
 *
 * Registers demand. Deliberately does NOT sell the expired deal at its old
 * price: if any past Yoink could be resurrected on demand, nothing would ever
 * actually be gone and the countdown on today's deal would mean nothing. This
 * asks the same question and answers it with data.
 *
 * Posts through Shopify's app proxy, so the request is same-origin and signed —
 * the endpoint can trust it came from this storefront.
 *
 * Dedup is a localStorage marker. Someone determined can clear it and vote
 * again, which is fine: this is a signal used to decide what to re-run, not a
 * ballot. Pretending otherwise would mean asking people to log in to express
 * interest, which would collect far less of it.
 */

const STORAGE_PREFIX = "yoink-voted:";

class AjBringBack extends HTMLElement {
  connectedCallback() {
    this.dealId = this.dataset.dealId;
    this.button = this.querySelector("button");
    this.countEl = this.querySelector("[data-vote-count]");
    if (!this.dealId || !this.button) return;

    // Reflect an existing vote immediately, so a reload does not invite a second
    // one and then quietly discard it.
    if (this.hasVoted()) this.markVoted();

    this.button.addEventListener("click", () => this.vote());
  }

  hasVoted() {
    try {
      return localStorage.getItem(STORAGE_PREFIX + this.dealId) === "1";
    } catch {
      return false; // private browsing; voting still works, dedup does not
    }
  }

  remember() {
    try {
      localStorage.setItem(STORAGE_PREFIX + this.dealId, "1");
    } catch {
      /* nothing to do */
    }
  }

  markVoted(votes) {
    this.button.disabled = true;
    this.button.textContent = "Asked for";
    if (votes != null && this.countEl) {
      this.countEl.textContent = this.countLabel(votes);
      this.countEl.hidden = false;
    }
  }

  countLabel(n) {
    return n === 1 ? "1 person wants this back" : `${n} people want this back`;
  }

  async vote() {
    if (this.hasVoted()) return;

    this.button.disabled = true;
    const original = this.button.textContent;
    this.button.textContent = "…";

    try {
      const res = await fetch("/apps/yoink/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dealId: this.dealId }),
      });
      const body = await res.json().catch(() => ({}));

      if (!res.ok || !body.ok) {
        // Re-enable rather than leave a dead button. Nothing was recorded, so
        // saying so and allowing a retry is the honest outcome.
        this.button.disabled = false;
        this.button.textContent = original;
        return;
      }

      this.remember();
      this.markVoted(body.votes);
    } catch {
      this.button.disabled = false;
      this.button.textContent = original;
    }
  }
}

if (!customElements.get("aj-bring-back")) {
  customElements.define("aj-bring-back", AjBringBack);
}
