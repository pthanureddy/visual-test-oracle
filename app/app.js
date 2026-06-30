const params = new URLSearchParams(window.location.search);
const bug = params.get("bug") || "clean";
const variant = params.get("variant") || "default";

const cartCount = document.querySelector("#cart-count");
const checkoutButton = document.querySelector("#checkout-btn");
const statusRegion = document.querySelector("#status-region");
const totalRow = document.querySelector("#total-row");
const totalPrice = document.querySelector("#total-price");
const itemPrice = document.querySelector("#item-price");

function applyVariant() {
  if (variant === "benign_copy") {
    checkoutButton.textContent = "Place order";
  }

  if (variant === "renamed_selector") {
    checkoutButton.id = "place-order-btn";
    checkoutButton.textContent = "Place order";
  }
}

function applyBugMode() {
  document.body.dataset.bug = bug;

  if (bug === "hidden_checkout") {
    checkoutButton.classList.add("is-hidden");
  }

  if (bug === "disabled_button") {
    checkoutButton.disabled = true;
  }

  if (bug === "missing_total") {
    totalRow.classList.add("is-hidden");
  }

  if (bug === "wrong_currency") {
    itemPrice.textContent = "€29.00";
    totalPrice.textContent = "€29.00";
  }

  if (bug === "layout_shift") {
    document.body.classList.add("bug-layout-shift");
  }

  if (bug === "overlap") {
    document.body.classList.add("bug-overlap");
  }
}

function confirmationClass() {
  if (bug === "wrong_color") {
    return "confirmation confirmation--warning";
  }
  if (bug === "extra_error") {
    return "confirmation confirmation--error";
  }
  return "confirmation";
}

function confirmationText() {
  if (bug === "wrong_copy") {
    return "Order delayed";
  }
  if (bug === "extra_error") {
    return "Payment review required";
  }
  return "Order placed";
}

function onCheckout() {
  if (bug !== "cart_not_reset") {
    cartCount.textContent = "0";
  }

  if (bug === "missing_confirmation") {
    statusRegion.replaceChildren();
    return;
  }

  const banner = document.createElement("div");
  banner.id = "confirmation-banner";
  banner.className = confirmationClass();
  banner.textContent = confirmationText();
  statusRegion.replaceChildren(banner);
}

applyVariant();
applyBugMode();
checkoutButton.addEventListener("click", onCheckout);
