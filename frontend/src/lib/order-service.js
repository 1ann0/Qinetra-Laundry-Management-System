// Price always follows the charged service quantity, not the number of pieces recorded.
export function getServiceQuantity(serviceLine) {
  return Number(serviceLine.quantity);
}
