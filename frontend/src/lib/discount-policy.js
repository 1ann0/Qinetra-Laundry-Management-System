// Use cents and percentage hundredths so the preview never rounds a ceiling up.
export function getRoundedServiceSubtotal(unitPrice, quantity) {
  const priceCents = Math.round(Number(unitPrice) * 100);
  const quantityHundredths = Math.round(Number(quantity) * 100);
  const product = priceCents * quantityHundredths;
  if (!Number.isSafeInteger(product) || priceCents < 0 || quantityHundredths < 0) return 0;
  // Match the API's rounding on each service, before adding the whole order.
  return Math.floor((product + 50) / 100) / 100;
}

export function getEmployeeDiscountAllowance(subtotal, percentage) {
  const cents = Math.round(Number(subtotal) * 100);
  const basisPoints = Math.round(Number(percentage) * 100);
  if (!Number.isSafeInteger(cents) || cents < 0 || !Number.isInteger(basisPoints) || basisPoints < 0 || basisPoints > 10000) return 0;
  return Math.floor(cents * basisPoints / 10000) / 100;
}

export function getDiscountPolicyError(role, policy, subtotal, discount) {
  if (role === "owner" || Number(discount) === 0) return "";
  if (!policy) return "The employee discount limit is unavailable. Reload before adding a discount.";
  const allowance = getEmployeeDiscountAllowance(subtotal, policy.employee_max_discount_percent);
  if (Math.round(Number(discount) * 100) > Math.round(allowance * 100)) {
    return `The whole-order discount must not exceed KES ${allowance.toFixed(2)} (${policy.employee_max_discount_percent}%). Reduce the discount or ask an owner to create the order.`;
  }
  return "";
}
