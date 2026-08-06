/**
 * <aj-cadence> — keeps the three calendar cards showing the right dates.
 *
 * WHY THIS EXISTS AT ALL. The section renders its dates in Liquid, from the
 * shop's own clock, which is correct at the moment the HTML is built. But this
 * is the homepage: it is the most-cached page on the store, and a cached copy
 * served two days later would point at a Tuesday that has already been and
 * gone. On a site whose entire promise is a rhythm, a calendar showing a stale
 * date is worse than no calendar.
 *
 * So the server render is the fallback — complete, correct at build time, and
 * fine with JavaScript off — and this element re-derives the dates on connect.
 *
 * THE OFFSET, NOT THE VISITOR'S TIMEZONE. What matters is the date in STORE
 * time: the tee drops Tuesday and the bin refills Thursday, both at 9am store
 * time. A shopper in Berlin at 01:00 is still on the store's Monday. The
 * section emits the store's UTC offset in minutes at render time and this
 * shifts the visitor's absolute clock by it.
 *
 * KNOWN LIMIT, DELIBERATELY ACCEPTED: that offset is sampled when the page is
 * built, so a copy cached across a daylight-saving change carries an offset one
 * hour stale. That can only move a date for someone loading the page within an
 * hour of store midnight on the changeover night, twice a year. The fix would
 * be shipping a full timezone database to move one numeral.
 */

const DAY_MS = 24 * 60 * 60 * 1000;

class AjCadence extends HTMLElement {
  connectedCallback() {
    const offsetMinutes = Number(this.dataset.storeOffsetMinutes);
    // Unparseable offset means we cannot say what the date is in store time,
    // and guessing prints a wrong number. Leave the server render alone.
    if (!Number.isFinite(offsetMinutes)) return;

    this.offsetMs = offsetMinutes * 60 * 1000;
    this.cards = Array.from(this.querySelectorAll('[data-cadence-card]'));
    if (!this.cards.length) return;

    this.sync();
    this.openOnTheYoink();

    // Re-check on the way back to a backgrounded tab: a phone left open
    // overnight is exactly the case the server render cannot cover.
    this.onVisible = () => {
      if (document.visibilityState === 'visible') this.sync();
    };
    document.addEventListener('visibilitychange', this.onVisible);
  }

  disconnectedCallback() {
    if (this.onVisible) document.removeEventListener('visibilitychange', this.onVisible);
  }

  /**
   * On a phone the three cards are a fan you swipe through, and it should open
   * on the Yoink rather than on Tuesday.
   *
   * DOM ORDER IS TUESDAY, YOINK, THURSDAY, and it stays that way: the reading
   * order is the argument the section makes, a screen reader should hear it in
   * that order, and the desktop layout depends on the daily card being the
   * middle grid column. So the card that greets a phone is chosen by scroll
   * position, not by reordering the list.
   *
   * `scrollLeft` RATHER THAN `scrollIntoView`. The latter scrolls every
   * scrollable ancestor, including the page — so landing on the homepage would
   * jump you down to this section before you had read anything above it. This
   * moves one scroller and touches nothing else.
   *
   * MEASURED WITH RECTS, NOT `offsetLeft`. This is the bug that made the deck
   * open on Tuesday no matter what. `offsetLeft` is measured from the nearest
   * POSITIONED ancestor, and the scroller is a plain `<ol>` with no positioning
   * — so the number coming back was the card's distance from somewhere else
   * entirely, usually the page. Bounding rects are measured against the
   * viewport, so the difference between the two is the real gap between them
   * whatever either element's offset parent happens to be.
   *
   * Silent when the cards are not a scroller. On desktop the container does not
   * overflow and the assignment is a no-op rather than a special case.
   *
   * RUN AGAIN AFTER LAYOUT SETTLES. The brand faces load as woff2 with
   * `font-display: block`, so the first measurement can happen while the cards
   * are still sized to a fallback. `fonts.ready` re-centres once they are not.
   */
  openOnTheYoink() {
    const scroller = this.querySelector('[data-cadence-scroller]');
    const hero = this.querySelector('[data-cadence-card]:not([data-cadence-weekday])');
    if (!scroller || !hero) return;

    const centre = () => {
      const s = scroller.getBoundingClientRect();
      const h = hero.getBoundingClientRect();
      const delta = h.left - s.left - (s.width - h.width) / 2;
      // Written without smooth behaviour on purpose: this is where the deck
      // STARTS, not somewhere it travels to while somebody is reading.
      scroller.scrollLeft += delta;
    };

    centre();
    if (document.fonts?.ready) document.fonts.ready.then(centre).catch(() => {});
  }

  sync() {
    // The store's wall clock, stamped as if it were UTC, so the getUTC* readers
    // below report the store's date rather than the browser's. Same trick as
    // schedule.ts in the app, for the same reason.
    const wall = new Date(Date.now() + this.offsetMs);

    for (const card of this.cards) {
      // Only the numeral moves. The day WORD is fixed — a card headed
      // "Tuesdays" is headed Tuesdays next week too — so it is server-rendered
      // once and never touched here.
      const numberEl = card.querySelector('[data-cadence-date]');
      const todayFlag = card.querySelector('[data-cadence-istoday]');

      const raw = card.dataset.cadenceWeekday;
      // The Everyday card has no weekday, which is also how openOnTheYoink
      // finds it. It is always today, and it carries no date numeral at all.
      const weekday = raw === '' || raw == null ? null : Number(raw);

      let target = wall;
      let isToday = true;
      if (weekday != null && Number.isFinite(weekday)) {
        // TODAY COUNTS AS THE NEXT ONE. On a Tuesday the tee card should read
        // Tuesday's date, not next week's — the drop is happening now, and
        // pointing at the one seven days away would be the section telling a
        // shopper to come back for something already on the page.
        const ahead = (weekday - wall.getUTCDay() + 7) % 7;
        target = new Date(wall.getTime() + ahead * DAY_MS);
        isToday = ahead === 0;
      }

      if (numberEl) numberEl.textContent = String(target.getUTCDate());
      if (todayFlag) todayFlag.hidden = !isToday;
      card.classList.toggle('is-today', isToday);
    }
  }
}

if (!customElements.get('aj-cadence')) {
  customElements.define('aj-cadence', AjCadence);
}
