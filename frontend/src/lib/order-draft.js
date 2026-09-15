import { ApiError } from "./user-messages.js";

const DRAFT_VERSION = 1;

export function orderDraftScope(userId) {
  return `qlms-order-draft:${userId}`;
}

export function hasMeaningfulOrderDraft(draft) {
  return Boolean(
    draft?.selectedCustomerId ||
      draft?.selectedServices?.length ||
      draft?.isEarlierOrder ||
      draft?.discountReason ||
      draft?.promisedReadyAt ||
      draft?.isPeakTime ||
      (draft?.paymentChoice && draft.paymentChoice !== "unpaid") ||
      draft?.depositAmount ||
      draft?.paymentConfirmed,
  );
}

export function readOrderDraft(storage, scope) {
  let raw;
  try {
    raw = storage.getItem(scope);
  } catch {
    throw new ApiError("QLMS could not check your unfinished order. Keep this page open and contact support.", 0, "QLMS-DRAFT-STORAGE");
  }
  if (!raw) return null;

  try {
    const saved = JSON.parse(raw);
    if (
      saved.version !== DRAFT_VERSION ||
      !saved.data ||
      typeof saved.data !== "object" ||
      !Array.isArray(saved.data.selectedServices)
    ) {
      throw new Error();
    }
    return saved.data;
  } catch {
    try {
      storage.removeItem(scope);
    } catch {
      // The actionable error below covers both invalid and inaccessible storage.
    }
    throw new ApiError("QLMS could not restore the unfinished order. Start it again and contact support if this returns.", 0, "QLMS-DRAFT-READ");
  }
}

export function saveOrderDraft(storage, scope, draft) {
  try {
    if (hasMeaningfulOrderDraft(draft)) {
      storage.setItem(scope, JSON.stringify({ version: DRAFT_VERSION, data: draft }));
    } else {
      storage.removeItem(scope);
    }
  } catch {
    throw new ApiError("QLMS could not protect this unfinished order. Keep this page open and contact support.", 0, "QLMS-DRAFT-STORAGE");
  }
}

export function clearOrderDraft(storage, scope) {
  try {
    storage.removeItem(scope);
  } catch {
    throw new ApiError("The order was saved, but QLMS could not clear its draft. Contact support before starting another order.", 0, "QLMS-DRAFT-CLEAR");
  }
}
