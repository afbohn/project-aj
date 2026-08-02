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

    outcomeEl.textContent = data.outcome;
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
