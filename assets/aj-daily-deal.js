/**
 * <aj-countdown> — counts down to a fixed, server-rendered deadline.
 *
 * The deadline arrives as an absolute UTC epoch (data-ends-at, in ms) written
 * by the daily_deal metaobject. That matters: every visitor sees the same
 * deadline, and a refresh does not restart the clock. A timer that resets per
 * session is the deceptive-urgency pattern we are deliberately not building —
 * it is also the version regulators take an interest in.
 *
 * Renders nothing on its own until connected, so the server-rendered markup
 * inside is the no-JS fallback (a plain "ends at <date>" line).
 */

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

class AjCountdown extends HTMLElement {
  connectedCallback() {
    const endsAt = Number(this.dataset.endsAt);

    // A missing or unparseable deadline leaves the server-rendered fallback in
    // place rather than showing a broken 00:00:00.
    if (!Number.isFinite(endsAt)) return;

    this.endsAt = endsAt;
    this.display = this.querySelector('[data-countdown-display]');
    if (!this.display) return;

    // Swap the fallback text for the live clock only once we know JS works.
    this.display.hidden = false;
    const fallback = this.querySelector('[data-countdown-fallback]');
    if (fallback) fallback.hidden = true;

    this.units = {
      days: this.querySelector('[data-unit="days"]'),
      hours: this.querySelector('[data-unit="hours"]'),
      minutes: this.querySelector('[data-unit="minutes"]'),
      seconds: this.querySelector('[data-unit="seconds"]'),
    };

    this.tick();
    // Align to the next whole second so the display does not visibly drift.
    this.timer = setInterval(() => this.tick(), SECOND);
  }

  disconnectedCallback() {
    clearInterval(this.timer);
  }

  tick() {
    const remaining = this.endsAt - Date.now();

    if (remaining <= 0) {
      this.expire();
      return;
    }

    const days = Math.floor(remaining / DAY);
    const hours = Math.floor((remaining % DAY) / HOUR);
    const minutes = Math.floor((remaining % HOUR) / MINUTE);
    const seconds = Math.floor((remaining % MINUTE) / SECOND);

    // The day group is hidden entirely for sub-24h deals, which is the normal
    // case for a daily deal — "0d 04:12:57" reads worse than "04:12:57".
    const dayGroup = this.units.days?.closest('[data-unit-group]');
    if (dayGroup) dayGroup.hidden = days === 0;

    this.set(this.units.days, days, false);
    this.set(this.units.hours, hours, days > 0);
    this.set(this.units.minutes, minutes, true);
    this.set(this.units.seconds, seconds, true);

    // One human-readable label for screen readers. The ticking digits
    // themselves are aria-hidden — announcing a new value every second makes
    // the page unusable with a screen reader.
    const label = this.querySelector('[data-countdown-label]');
    if (label) {
      const parts = [];
      if (days > 0) parts.push(`${days} day${days === 1 ? '' : 's'}`);
      if (days > 0 || hours > 0) parts.push(`${hours} hour${hours === 1 ? '' : 's'}`);
      parts.push(`${minutes} minute${minutes === 1 ? '' : 's'}`);
      label.textContent = `${parts.join(', ')} remaining`;
    }
  }

  set(el, value, pad) {
    if (!el) return;
    const next = pad ? String(value).padStart(2, '0') : String(value);
    if (el.textContent !== next) el.textContent = next;
  }

  expire() {
    clearInterval(this.timer);

    this.dispatchEvent(new CustomEvent('aj:deal-expired', { bubbles: true }));

    const expired = this.querySelector('[data-countdown-expired]');
    if (expired) {
      expired.hidden = false;
      if (this.display) this.display.hidden = true;
    }

    // Only reload when the section asks for it. The server has to re-resolve
    // which deal is active, and there is no way to do that client-side — but
    // reloading a page out from under someone mid-scroll is rude, so this is
    // opt-in and delayed.
    if (this.hasAttribute('data-reload-on-expire')) {
      setTimeout(() => window.location.reload(), 5000);
    }
  }
}

if (!customElements.get('aj-countdown')) {
  customElements.define('aj-countdown', AjCountdown);
}
