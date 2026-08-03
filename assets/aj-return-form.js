/*
  Return form — two steps, one endpoint.

  Everything posts to /apps/yoink/return, Shopify's app proxy, which signs the
  request on the way through. Same origin, so no CORS, and the app can tell the
  difference between our storefront and the rest of the internet.

  THE SERVER DECIDES, THIS FILE ONLY ASKS. No pricing, no policy and no
  eligibility logic lives here — it would be visible to anyone with a browser
  and, worse, it would be a second copy of rules that already exist in
  app/lib/returns.ts. The page shows whatever the server says.
*/

const root = document.querySelector(".aj-rf");
if (root) {
  const find = root.querySelector('[data-step="find"]');
  const items = root.querySelector('[data-step="items"]');
  const result = root.querySelector("[data-result]");
  const errorEl = root.querySelector("[data-error]");
  const itemsBox = root.querySelector("[data-items]");
  const foundEl = root.querySelector("[data-found]");
  const outcomeEl = root.querySelector("[data-outcome]");

  let order = "";
  let email = "";

  const showError = (message) => {
    errorEl.textContent = message;
    errorEl.hidden = false;
  };
  const clearError = () => {
    errorEl.hidden = true;
    errorEl.textContent = "";
  };

  const post = async (body) => {
    const res = await fetch("/apps/yoink/return", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    // A proxy misconfiguration returns HTML, and JSON.parse on a login page is
    // a confusing way to find that out.
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      return { ok: false, message: "Returns aren't available right now. Please email us." };
    }
  };

  const money = (n) => `$${Number(n).toFixed(2)}`;

  find.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();
    const button = find.querySelector("[data-find]");
    button.disabled = true;
    button.textContent = "Looking…";

    order = find.querySelector("#aj-rf-order").value.trim();
    email = find.querySelector("#aj-rf-email").value.trim();

    const data = await post({ action: "lookup", orderNumber: order, email });
    button.disabled = false;
    button.textContent = "Find my order";

    if (!data.ok) return showError(data.message || "We couldn't find that order.");

    foundEl.textContent = `${data.orderName} — pick what you're sending back.`;
    itemsBox.innerHTML = data.items
      .map(
        (it, i) => `
        <label class="aj-rf__item">
          <input type="checkbox" name="item" value="${it.id}" data-max="${it.quantity}"
                 ${data.items.length === 1 ? "checked" : ""} id="aj-rf-item-${i}">
          <span>${it.title}</span>
          <small>${it.quantity > 1 ? `${it.quantity} × ` : ""}${money(it.unitPrice)}</small>
        </label>`,
      )
      .join("");

    find.hidden = true;
    items.hidden = false;
    items.querySelector("#aj-rf-reason").focus();
  });

  items.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    const chosen = [...itemsBox.querySelectorAll("input[name=item]:checked")].map((el) => ({
      id: el.value,
      quantity: Number(el.dataset.max) || 1,
    }));
    if (!chosen.length) return showError("Pick at least one item to return.");

    const button = items.querySelector("[data-submit]");
    button.disabled = true;
    button.textContent = "Sending…";

    const data = await post({
      action: "submit",
      orderNumber: order,
      email,
      items: chosen,
      reason: items.querySelector("#aj-rf-reason").value,
    });

    button.disabled = false;
    button.textContent = "Request the return";

    if (!data.ok) return showError(data.message || "That didn't go through. Try again.");

    // The server offers keep-it rather than deciding it. Show the options and
    // let them pick; nothing is recorded until they do.
    if (data.choose) {
      const box = root.querySelector("[data-choice]");
      root.querySelector("[data-choice-lead]").textContent = data.keepItReason;
      root.querySelector("[data-choice-options]").innerHTML = data.options
        .map(
          (o) => `<button type="button" class="aj-rf__opt" data-pick="${o.key}">
                    <strong>${o.label}</strong><small>${o.detail}</small>
                  </button>`,
        )
        .join("");
      items.hidden = true;
      box.hidden = false;
      box.querySelectorAll("[data-pick]").forEach((b) =>
        b.addEventListener("click", async () => {
          box.querySelectorAll("[data-pick]").forEach((x) => (x.disabled = true));
          const picked = await post({
            action: "choose",
            orderNumber: order,
            email,
            settlement: b.dataset.pick,
            value: data.value,
            reason: data.reason,
            itemsSummary: foundEl.textContent,
          });
          if (!picked.ok) {
            box.querySelectorAll("[data-pick]").forEach((x) => (x.disabled = false));
            return showError(picked.message || "That didn't go through.");
          }
          box.hidden = true;
          outcomeEl.textContent = picked.outcome;
          root.querySelector("[data-note]").hidden = true;
          result.hidden = false;
          result.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }),
      );
      return;
    }

    outcomeEl.textContent = data.outcome;
    // Only say "check your email" when something will actually send one:
    // Shopify emails the label on a created return. A keep-it decision creates
    // no return, so there is nothing to watch the inbox for.
    const note = root.querySelector("[data-note]");
    if (data.action === "refund_cash") {
      note.textContent = "Watch your email for the label.";
      note.hidden = false;
    } else {
      note.hidden = true;
    }
    items.hidden = true;
    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });

  root.querySelector("[data-back]").addEventListener("click", () => {
    clearError();
    items.hidden = true;
    find.hidden = false;
  });
}
