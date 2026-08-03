/**
 * The Yoink of the Day image gallery.
 *
 * PROGRESSIVE, NOT LOAD-BEARING. The track is a scroll container with CSS
 * snap points, so it already swipes and snaps with this file absent. Everything
 * here is the affordance layer: the dots that say more images exist, and the
 * arrows a mouse needs because it cannot swipe. If this never loads, the
 * gallery still works and only looks like a single image.
 *
 * DOTS ARE BUILT HERE RATHER THAN IN LIQUID because the slide count is only
 * knowable after deduplication — the variant hero is often also in
 * `product.media`, and Liquid would have to walk the list twice to count what
 * survives. The DOM already holds the answer.
 *
 * NO LIBRARY. This is one scroll container, one IntersectionObserver and two
 * buttons; a carousel dependency would be more bytes than the images it pages
 * through.
 */

class AjDealGallery {
  constructor(root) {
    this.root = root;
    this.track = root.querySelector("[data-aj-gallery-track]");
    this.dotsEl = root.querySelector("[data-aj-gallery-dots]");
    this.prev = root.querySelector("[data-aj-gallery-prev]");
    this.next = root.querySelector("[data-aj-gallery-next]");
    if (!this.track) return;

    this.slides = [...this.track.querySelectorAll(".aj-deal__slide")];
    // The real count, after Liquid has skipped the duplicate hero. The CSS
    // hides the controls off this, so it has to be corrected from the DOM
    // rather than left at the pre-dedup number the template rendered.
    this.root.dataset.count = String(this.slides.length);
    if (this.slides.length < 2) return;

    this.index = 0;
    this.#buildDots();
    this.#wireArrows();
    this.#wireVariantReset();
    // Set the opening state explicitly. The observer does fire for the visible
    // slide, but not before the first paint — measured on the live page, `prev`
    // sat enabled on slide one, which is an arrow that looks clickable and does
    // nothing. #watch() comes after so the observer only ever corrects this.
    this.#mark(0);
    this.#watch();
  }

  #buildDots() {
    this.dots = this.slides.map((_, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "aj-deal__dot";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-label", `Image ${i + 1} of ${this.slides.length}`);
      b.setAttribute("aria-selected", i === 0 ? "true" : "false");
      b.addEventListener("click", () => this.#go(i));
      this.dotsEl?.appendChild(b);
      return b;
    });
  }

  /*
   * IntersectionObserver rather than a scroll listener. A scroll handler on a
   * snapping container fires continuously through the gesture and has to be
   * debounced into guessing which slide "won"; the observer just reports the
   * one that is actually on screen, including after a native swipe we never
   * initiated.
   */
  #watch() {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          const i = this.slides.indexOf(e.target);
          if (i >= 0) this.#mark(i);
        }
      },
      { root: this.track, threshold: 0.6 },
    );
    this.slides.forEach((s) => io.observe(s));
    this.io = io;
  }

  #mark(i) {
    this.index = i;
    this.dots?.forEach((d, n) => d.setAttribute("aria-selected", n === i ? "true" : "false"));
    // Disabled at the ends rather than wrapping: a gallery that silently loops
    // gives no sense of how much is left, and on three images that matters.
    if (this.prev) this.prev.disabled = i === 0;
    if (this.next) this.next.disabled = i === this.slides.length - 1;
  }

  #go(i) {
    const target = this.slides[i];
    if (!target) return;
    // scrollIntoView would also scroll the PAGE to bring the deal card into
    // view, which yanks the layout when someone clicks a dot after scrolling
    // past. Setting scrollLeft moves only the track.
    this.track.scrollTo({
      left: target.offsetLeft - this.track.offsetLeft,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    });
  }

  #wireArrows() {
    this.prev?.addEventListener("click", () => this.#go(Math.max(0, this.index - 1)));
    this.next?.addEventListener("click", () =>
      this.#go(Math.min(this.slides.length - 1, this.index + 1)));
  }

  /*
   * A variant change rewrites the first slide's image in place (see
   * aj-variant-select.js). Someone sitting on slide three would keep looking at
   * the previous colour's photo, so the gallery returns to the hero — which is
   * the image that just changed.
   */
  #wireVariantReset() {
    const hero = this.track.querySelector("[data-aj-variant-image] img");
    if (!hero || !("MutationObserver" in window)) return;
    new MutationObserver(() => this.#go(0)).observe(hero, {
      attributes: true,
      attributeFilter: ["src", "srcset"],
    });
  }
}

const boot = () =>
  document.querySelectorAll("[data-aj-gallery]").forEach((el) => {
    if (el.dataset.ajGalleryReady) return;
    el.dataset.ajGalleryReady = "1";
    new AjDealGallery(el);
  });

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

// Section re-render in the theme editor, and cart/section morphs, replace the
// markup wholesale — without this the gallery would come back inert.
document.addEventListener("shopify:section:load", boot);
