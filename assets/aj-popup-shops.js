/*
  AJ Pop-up Shops — turns the page.

  THE CUSTOMER TURNS IT. That is the interaction, and everything here serves it:
  arrows, a swipe, arrow keys, and the tabs as a jump to a named shop. The
  auto-advance is off unless the section asks for it, and it stops for good the
  moment somebody does anything — a book that keeps turning itself while you are
  reading a page is a book arguing with you.

  ONE SEQUENCE, THREE BEATS, AND THE ORDER IS THE ILLUSION:
    1. the standing shop folds flat into the gutter   (it must be DOWN first —
       a page sweeping through a card standing upright is the single frame that
       destroys the whole effect)
    2. the leaf sweeps across
    3. the next shop rises as the leaf lands

  IT IS NOT REENTRANT AND IT MUST NOT BE. `turning` gates the whole sequence, so
  a fast double-click or a flick queues nothing: the second press is dropped
  rather than starting a second turn on top of the first, which would leave a
  folded card and a standing leaf.

  WHAT THIS FILE IS ALLOWED TO DO: reveal the book and change which shop is
  standing. It builds no markup and owns no links — every shop is already an
  anchor in the DOM before this runs, which is why the section degrades to a
  plain list rather than to nothing when the asset fails to load.
*/
(function () {
  var REDUCED =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Matches --aj-popup-turn and the fold in the stylesheet. Kept here as
     numbers because the sequencing is in JS; if either changes, change both. */
  var TURN_MS = REDUCED ? 0 : 700;
  var FOLD_MS = REDUCED ? 0 : 300;

  function setup(root) {
    if (root.dataset.ajReady === "1") return;
    root.dataset.ajReady = "1";

    var pops = Array.prototype.slice.call(root.querySelectorAll("[data-aj-pop]"));
    var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-aj-tab]"));
    var struts = root.querySelector("[data-aj-struts]");
    var cast = root.querySelector("[data-aj-cast]");
    var leaf = root.querySelector("[data-aj-leaf]");
    var prev = root.querySelector("[data-aj-prev]");
    var next = root.querySelector("[data-aj-next]");
    var counter = root.querySelector("[data-aj-count]");
    if (!pops.length) return;

    var index = 0;
    var turning = false;
    var timer = null;
    var auto = root.getAttribute("data-auto") === "true" && !REDUCED;
    var interval = (Number(root.getAttribute("data-interval")) || 5) * 1000;

    // Only now does the book replace the plain list: a parse error above this
    // line leaves the links visible instead of hiding them behind a book that
    // never opens.
    root.classList.add("aj-popup--ready");

    function paint() {
      tabs.forEach(function (tab, i) {
        tab.setAttribute("aria-selected", i === index ? "true" : "false");
      });
      pops.forEach(function (pop, i) {
        pop.setAttribute("aria-hidden", i === index ? "false" : "true");
      });
      if (counter) counter.textContent = index + 1 + " / " + pops.length;
      // The book wraps, so neither control is ever dead — but with one shop
      // there is nothing to turn to.
      if (prev) prev.disabled = pops.length < 2;
      if (next) next.disabled = pops.length < 2;
    }

    function raise(i) {
      pops[i].classList.add("is-open");
      if (struts) struts.classList.add("is-open");
      // The shadow lies on the page and belongs to whatever is standing, so it
      // is raised and folded with the piece rather than living inside it.
      if (cast) cast.classList.add("is-open");
    }

    function turn(to, forwards) {
      if (turning || to === index || pops.length < 2) return;
      turning = true;

      // 1. fold what is standing
      pops[index].classList.remove("is-open");
      if (struts) struts.classList.remove("is-open");
      if (cast) cast.classList.remove("is-open");

      window.setTimeout(function () {
        // 2. sweep the leaf
        if (leaf && !REDUCED) {
          leaf.classList.add(forwards ? "is-turning" : "is-turning-back");
        }

        window.setTimeout(function () {
          if (leaf) {
            leaf.classList.remove("is-turning", "is-turning-back");
          }
          index = to;
          paint();
          // 3. the next shop rises out of the fresh page
          raise(index);
          turning = false;
        }, TURN_MS);
      }, FOLD_MS);
    }

    function go(delta, byHuman) {
      if (byHuman) stopAuto(true);
      var to = (index + delta + pops.length) % pops.length;
      turn(to, delta > 0);
    }

    function stopAuto(forGood) {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
      if (forGood) auto = false;
    }

    function startAuto() {
      if (!auto || timer || pops.length < 2) return;
      timer = window.setInterval(function () {
        go(1, false);
      }, interval);
    }

    if (prev) prev.addEventListener("click", function () { go(-1, true); });
    if (next) next.addEventListener("click", function () { go(1, true); });

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () {
        stopAuto(true);
        turn(i, i > index);
      });
    });

    // Arrow keys, when the book itself has focus. Scoped to the section so it
    // never steals the arrows from the page.
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(1, true); }
      if (e.key === "ArrowLeft") { e.preventDefault(); go(-1, true); }
    });

    // Swipe. A book on a phone should turn with a thumb, and 45px is far enough
    // that a vertical scroll does not register as a page turn.
    var startX = null;
    var startY = null;
    root.addEventListener(
      "touchstart",
      function (e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      },
      { passive: true },
    );
    root.addEventListener(
      "touchend",
      function (e) {
        if (startX == null) return;
        var dx = e.changedTouches[0].clientX - startX;
        var dy = e.changedTouches[0].clientY - startY;
        startX = null;
        if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy)) return;
        go(dx < 0 ? 1 : -1, true);
      },
      { passive: true },
    );

    paint();
    raise(0);

    if (!auto) return;
    if (!("IntersectionObserver" in window)) {
      startAuto();
      return;
    }
    // Do not turn pages nobody is looking at: a book that has been advancing
    // above the fold since load presents whichever shop it landed on, and the
    // first one — the one chosen deliberately — is the one nobody sees.
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) startAuto();
          else stopAuto(false);
        });
      },
      { threshold: 0.35 },
    );
    io.observe(root);

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stopAuto(false);
      else startAuto();
    });
  }

  function init(scope) {
    (scope || document).querySelectorAll("[data-aj-popup]").forEach(setup);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { init(); });
  } else {
    init();
  }

  // The theme editor tears a section down and rebuilds it on every setting
  // change; without this the rebuilt book never opens.
  document.addEventListener("shopify:section:load", function (event) {
    init(event.target);
  });
})();
