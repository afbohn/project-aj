/*
  The pointer tilt on the collector slab.

  IT WRITES TWO CUSTOM PROPERTIES AND NEVER TOUCHES `transform` — the CSS keeps
  ownership of how the rotations compose. The resting lean is `rotate` and the
  hover lift is `translate`/`scale`, which are independent properties; if this
  set `transform` wholesale a pointermove would overwrite the lift on its next
  frame and the slab would drop mid-hover.

  EVERY SLAB ON THE PAGE, not one section's. The inline version this replaces
  looked up `#shopify-section-{{ section.id }}`, which was correct while the slab
  existed only on the homepage. The product page has no such wrapper, so the
  binding is per-slab instead — and the file is idempotent, so loading it from
  both callers on a page that somehow had both costs one no-op pass.
*/
(function () {
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var MAX = 9; // degrees; past ~12 the case reads as a glitch rather than a tilt

  function bind(slab) {
    if (slab.dataset.ajTiltBound) return;
    var stage = slab.closest('.aj-teew__stage');
    if (!stage) return;
    slab.dataset.ajTiltBound = '1';

    var frame = null;

    function track(event) {
      if (frame) return;
      frame = requestAnimationFrame(function () {
        frame = null;
        var box = slab.getBoundingClientRect();
        if (!box.width || !box.height) return;
        var px = (event.clientX - box.left) / box.width - 0.5;
        var py = (event.clientY - box.top) / box.height - 0.5;
        slab.style.setProperty('--aj-teew-ry', (px * MAX * 2).toFixed(2) + 'deg');
        slab.style.setProperty('--aj-teew-rx', (py * -MAX * 2).toFixed(2) + 'deg');
      });
    }

    function release() {
      if (frame) {
        cancelAnimationFrame(frame);
        frame = null;
      }
      slab.style.setProperty('--aj-teew-ry', '0deg');
      slab.style.setProperty('--aj-teew-rx', '0deg');
    }

    stage.addEventListener('pointermove', track);
    stage.addEventListener('pointerleave', release);
  }

  function scan() {
    document.querySelectorAll('[data-aj-tilt]').forEach(bind);
  }

  scan();
  /* The theme editor re-renders a section in place, which replaces the slab
     node and drops the listeners with it. Cheap to re-scan. */
  document.addEventListener('shopify:section:load', scan);
})();
