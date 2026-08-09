/**
 * Carries the Meta click id from the ad click to the signup, so a Lead can be
 * attributed to the ad that caused it.
 *
 * WHY THIS EXISTS. The Conversions API is already reporting every signup from
 * `webhooks.customers.create`, and it works — the pixel received 17 Lead events
 * over 8-9 Aug. Meta still credited its campaigns with ONE, because the only
 * thing those events carried about the person was a hashed email. An email
 * matches an account; it does not say which ad was clicked. Without a click id
 * Meta will not join the two, so the campaign optimising toward signups is
 * learning from a single data point while the store takes seven a day.
 *
 * THE PIXEL CANNOT DO THIS ITSELF. Shopify serves it through a sandboxed Web
 * Pixel running in its own worker, so there is no `fbq` in page scope and no
 * theme code can reach it. `_fbc` therefore never gets written where we can
 * read it, which is why this stores its own first-party copy.
 *
 * THE CLICK AND THE SIGNUP ARE DIFFERENT PAGES. An ad lands on the homepage or
 * a product; the email is handed over later, often on /pages/join, and often
 * not in the same minute. So the id is persisted in a first-party cookie at the
 * moment of landing and read back at the moment of submitting. 90 days, which
 * is Meta's own click attribution window — a cookie that expired sooner would
 * silently drop the slowest and most valuable conversions.
 *
 * THE CHANNEL IS `contact[tags]`, because every signup form on this store is
 * Shopify's own `{% form 'customer' %}` and tags are the one arbitrary field it
 * will carry from the browser to the customer record. The app strips these tags
 * off again once the event is sent, so they never accumulate on a customer or
 * pollute the tag list the other agents read.
 *
 * IT NEVER BLOCKS A SIGNUP. Every step is wrapped: a blocked cookie, a private
 * window, a malformed URL — all of them end with the form submitting exactly as
 * it would have. An unattributed email is a small loss; a form that throws on
 * submit is the whole business.
 */

(function () {
  var FBC_COOKIE = '_yoink_fbc';
  var DAYS = 90;

  function readCookie(name) {
    try {
      var hit = document.cookie.split('; ').find(function (row) {
        return row.indexOf(name + '=') === 0;
      });
      return hit ? decodeURIComponent(hit.slice(name.length + 1)) : null;
    } catch (e) {
      return null;
    }
  }

  function writeCookie(name, value) {
    try {
      var expires = new Date(Date.now() + DAYS * 864e5).toUTCString();
      document.cookie =
        name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/; SameSite=Lax';
    } catch (e) {
      /* Cookies refused. The signup still works, it just arrives anonymous. */
    }
  }

  /*
    Meta's own format: fb.<subdomainIndex>.<clickTime>.<fbclid>. The timestamp
    must be when the CLICK happened rather than when the form was submitted,
    which is the whole reason this is stamped here on landing instead of being
    reconstructed later from the signup time.
  */
  function captureClickId() {
    try {
      var fbclid = new URLSearchParams(window.location.search).get('fbclid');
      if (!fbclid) return;
      writeCookie(FBC_COOKIE, 'fb.1.' + Date.now() + '.' + fbclid);
    } catch (e) {
      /* No URLSearchParams, or a URL we cannot parse. Nothing to carry. */
    }
  }

  /*
    `_fbp` is the sandboxed pixel's own browser id. We cannot write it and must
    not invent it — but if Shopify's pixel has set one on this domain it is
    readable, and it is the second-best join key Meta has after a click id. Sent
    when present, absent otherwise, never fabricated.
  */
  function browserId() {
    return readCookie('_fbp');
  }

  function decorate(form) {
    try {
      if (!form || !form.querySelector('input[name="contact[email]"]')) return;

      var extra = [];
      var fbc = readCookie(FBC_COOKIE);
      var fbp = browserId();
      if (fbc) extra.push('fbc-' + fbc);
      if (fbp) extra.push('fbp-' + fbp);
      if (!extra.length) return;

      var field = form.querySelector('input[name="contact[tags]"]');
      if (!field) {
        // Every signup form on this store ships one, but a new form that
        // forgets it should still be attributable rather than silently not.
        field = document.createElement('input');
        field.type = 'hidden';
        field.name = 'contact[tags]';
        field.value = '';
        form.appendChild(field);
      }

      // APPENDED, NEVER REPLACED. That field already carries the tag naming the
      // signup surface — `join-page`, `popup`, `list`, `yoink-preview` — and
      // those are what the welcome path and the reporting are keyed on.
      var current = (field.value || '').split(',').map(function (t) {
        return t.trim();
      }).filter(Boolean);

      extra.forEach(function (t) {
        if (current.indexOf(t) === -1) current.push(t);
      });
      field.value = current.join(',');
    } catch (e) {
      /* Submit unmodified rather than not at all. */
    }
  }

  captureClickId();

  /*
    Bound once on the document rather than per form, in the capture phase: the
    popup and the tomorrow-teaser inject their forms after this script has run,
    and a listener attached at load would never see them.
  */
  document.addEventListener(
    'submit',
    function (event) {
      decorate(event.target);
    },
    true,
  );
})();
