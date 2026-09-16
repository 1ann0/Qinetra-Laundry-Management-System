"use client";

import { getUserMessage } from "@/lib/user-messages";

import { useState } from "react";

// Keep the usual Laundry tally items in the order provided by Qinetra.
const LAUNDRY_TALLY_ORDER = [
  "Shirt",
  "T-shirt",
  "Trouser",
  "Jacket",
  "Socks (Pair)",
  "Single Sock",
  "Underwear",
  "Blouse",
  "Bedsheet",
  "Vest",
  "Pillowcase",
  "Shorts",
  "Bra",
  "Towel",
];

function sortLaundryTallyItems(itemTypes) {
  return [...itemTypes].sort((first, second) => {
    const firstPosition = LAUNDRY_TALLY_ORDER.indexOf(first.name);
    const secondPosition = LAUNDRY_TALLY_ORDER.indexOf(second.name);
    const firstIsKnown = firstPosition !== -1;
    const secondIsKnown = secondPosition !== -1;

    if (firstIsKnown && secondIsKnown) return firstPosition - secondPosition;
    if (firstIsKnown) return -1;
    if (secondIsKnown) return 1;
    return first.name.localeCompare(second.name);
  });
}

// Create one empty garment record for a detailed cleaning service.
export function createBlankGarment(localId = 1, itemTypeId = "") {
  return {
    localId,
    existing_item_id: null,
    garment_reference: null,
    item_type_id: itemTypeId,
    description: "",
    is_damaged: "",
    damage_note: "",
    stain_note: "",
  };
}

export function createBlankTallyException(localId = 1) {
  return {
    localId,
    description: "",
    is_damaged: false,
    damage_note: "",
    stain_note: "",
  };
}

// Display the clothing controls selected in the owner's service setup.
export default function ServiceItemEntry({
  recordingMode,
  itemTypes,
  items,
  onItemsChange,
  disabled,
  fieldPrefix,
  allowedInactiveItemTypeIds = [],
  fixedItemType = null,
  onAddMissingItem = null,
}) {
  const [showMissingItemForm, setShowMissingItemForm] = useState(false);
  const [missingItemName, setMissingItemName] = useState("");
  const [missingItemFeedback, setMissingItemFeedback] = useState(null);
  const [isAddingMissingItem, setIsAddingMissingItem] = useState(false);

  // Keep Laundry tally choices separate from Dry Cleaning garment choices.
  // Old receipt items stay visible even if their catalogue setting later changes.
  const allowedInactiveIds = new Set(allowedInactiveItemTypeIds);
  const expectedItemGroup =
    recordingMode === "tally" ? "laundry" : "dry_cleaning";
  const visibleItemTypes = itemTypes.filter(
    (itemType) =>
      allowedInactiveIds.has(itemType.id) ||
      (itemType.is_active !== false &&
        [expectedItemGroup, "both"].includes(itemType.item_group)),
  );
  const tallyItemTypes = sortLaundryTallyItems(visibleItemTypes);

  // Add or remove one piece from the quick tally.
  function changeTally(itemTypeId, amount) {
    const currentItem = items.find(
      (item) => item.item_type_id === itemTypeId,
    );
    const exceptionCount = currentItem?.exceptions?.length || 0;
    const nextQuantity = Math.max(
      exceptionCount,
      (currentItem?.quantity || 0) + amount,
    );
    const otherItems = items.filter(
      (item) => item.item_type_id !== itemTypeId,
    );

    onItemsChange(
      nextQuantity > 0
        ? [
            ...otherItems,
            {
              ...currentItem,
              item_type_id: itemTypeId,
              quantity: nextQuantity,
              exceptions: currentItem?.exceptions || [],
            },
          ]
        : otherItems,
    );
  }

  // A condition exception describes one counted piece and never adds to the tally.
  function addTallyException(itemTypeId) {
    onItemsChange(items.map((item) => {
      if (item.item_type_id !== itemTypeId) return item;
      const currentExceptions = item.exceptions || [];
      if (currentExceptions.length >= item.quantity) return item;
      const nextLocalId = currentExceptions.reduce(
        (largestId, exception) =>
          Math.max(largestId, Number(exception.localId) || 0),
        0,
      ) + 1;
      return {
        ...item,
        exceptions: [
          ...currentExceptions,
          createBlankTallyException(nextLocalId),
        ],
      };
    }));
  }

  function updateTallyException(itemTypeId, localId, field, value) {
    onItemsChange(items.map((item) => {
      if (item.item_type_id !== itemTypeId) return item;
      return {
        ...item,
        exceptions: (item.exceptions || []).map((exception) => {
          if (exception.localId !== localId) return exception;
          const nextException = { ...exception, [field]: value };
          if (field === "is_damaged" && !value) {
            nextException.damage_note = "";
          }
          return nextException;
        }),
      };
    }));
  }

  function removeTallyException(itemTypeId, localId) {
    onItemsChange(items.map((item) =>
      item.item_type_id === itemTypeId
        ? {
            ...item,
            exceptions: (item.exceptions || []).filter(
              (exception) => exception.localId !== localId,
            ),
          }
        : item,
    ));
  }

  // Save a new shop-wide Laundry choice, then count it once on this service.
  async function addMissingTallyItem(event) {
    event.preventDefault();
    const cleanedName = missingItemName.trim();

    if (!cleanedName) {
      setMissingItemFeedback({
        type: "error",
        text: "Enter the clothing item name.",
      });
      return;
    }

    setIsAddingMissingItem(true);
    setMissingItemFeedback(null);

    try {
      const savedItem = await onAddMissingItem(cleanedName);
      changeTally(savedItem.id, 1);
      setMissingItemName("");
      setShowMissingItemForm(false);
      setMissingItemFeedback({
        type: "success",
        text: `${savedItem.name} was added to the shop tally and counted once.`,
      });
    } catch (saveError) {
      setMissingItemFeedback({
        type: "error",
        text: getUserMessage(saveError, "QLMS could not confirm the new clothing item. Check the clothing list before you add it again."),
      });
    } finally {
      setIsAddingMissingItem(false);
    }
  }

  // Add another garment card to a detailed service.
  function addGarment() {
    const nextLocalId =
      items.reduce(
        (largestId, item) => Math.max(largestId, Number(item.localId) || 0),
        0,
      ) + 1;
    onItemsChange([
      ...items,
      createBlankGarment(nextLocalId, fixedItemType?.id || ""),
    ]);
  }

  // Change one field without affecting the other garment records.
  function updateGarment(localId, field, value) {
    onItemsChange(
      items.map((item) => {
        if (item.localId !== localId) {
          return item;
        }

        const updatedItem = { ...item, [field]: value };
        if (field === "is_damaged" && value !== "true") {
          updatedItem.damage_note = "";
        }
        return updatedItem;
      }),
    );
  }

  // Remove a garment that was added by mistake.
  function removeGarment(localId) {
    onItemsChange(items.filter((item) => item.localId !== localId));
  }

  if (recordingMode === "tally") {
    const totalPieces = items.reduce(
      (total, item) => total + item.quantity,
      0,
    );

    return (
      <section className="mt-5 rounded-xl border border-blue-200 bg-blue-50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h4 className="font-bold text-slate-900">Clothing tally</h4>
            <p className="mt-1 text-sm text-slate-600">
              Count each piece while checking the customer&apos;s laundry.
            </p>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-sm font-bold text-[#005AAB]">
            {totalPieces} {totalPieces === 1 ? "piece" : "pieces"}
          </span>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {tallyItemTypes.map((itemType) => {
            const tallyItem = items.find(
              (item) => item.item_type_id === itemType.id,
            );
            const quantity = tallyItem?.quantity || 0;
            const exceptions = tallyItem?.exceptions || [];

            return (
              <article
                className="rounded-lg border border-blue-100 bg-white px-3 py-2"
                key={itemType.id}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-slate-800">
                    {itemType.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                      type="button"
                      aria-label={`Remove one ${itemType.name}`}
                      disabled={disabled || quantity <= exceptions.length}
                      onClick={() => changeTally(itemType.id, -1)}
                    >
                      −
                    </button>
                    <span
                      className="w-6 text-center font-bold text-slate-900"
                      aria-label={`${itemType.name} quantity`}
                    >
                      {quantity}
                    </span>
                    <button
                      className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#005AAB] font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-40"
                      type="button"
                      aria-label={`Add one ${itemType.name}`}
                      disabled={disabled}
                      onClick={() => changeTally(itemType.id, 1)}
                    >
                      +
                    </button>
                  </div>
                </div>

                {quantity > 0 ? (
                  <button
                    className="mt-2 text-left text-xs font-bold text-[#005AAB] hover:underline disabled:opacity-50"
                    type="button"
                    disabled={disabled || exceptions.length >= quantity}
                    onClick={() => addTallyException(itemType.id)}
                  >
                    Add damage or stain note
                  </button>
                ) : null}

                {exceptions.map((exception, index) => (
                  <div
                    className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3"
                    key={exception.localId}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-bold text-amber-950">
                        Affected {itemType.name.toLowerCase()} {index + 1}
                      </p>
                      <button
                        className="text-xs font-bold text-red-700 hover:underline"
                        type="button"
                        disabled={disabled}
                        onClick={() =>
                          removeTallyException(itemType.id, exception.localId)
                        }
                      >
                        Remove note
                      </button>
                    </div>
                    <label
                      className="mt-3 block text-xs font-semibold text-slate-800"
                      htmlFor={`${fieldPrefix}-${itemType.id}-exception-${exception.localId}-description`}
                    >
                      Which item?
                    </label>
                    <input
                      className="mt-1 min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                      id={`${fieldPrefix}-${itemType.id}-exception-${exception.localId}-description`}
                      maxLength="200"
                      placeholder="Example: Blue school shirt"
                      value={exception.description}
                      disabled={disabled}
                      onChange={(event) => updateTallyException(
                        itemType.id,
                        exception.localId,
                        "description",
                        event.target.value,
                      )}
                    />
                    <label className="mt-3 flex items-center gap-2 text-xs font-semibold text-slate-800">
                      <input
                        type="checkbox"
                        checked={exception.is_damaged}
                        disabled={disabled}
                        onChange={(event) => updateTallyException(
                          itemType.id,
                          exception.localId,
                          "is_damaged",
                          event.target.checked,
                        )}
                      />
                      Existing damage
                    </label>
                    {exception.is_damaged ? (
                      <input
                        aria-label={`Existing damage on ${itemType.name} ${index + 1}`}
                        className="mt-2 min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                        maxLength="300"
                        placeholder="Describe the tear, hole or other damage"
                        value={exception.damage_note}
                        disabled={disabled}
                        onChange={(event) => updateTallyException(
                          itemType.id,
                          exception.localId,
                          "damage_note",
                          event.target.value,
                        )}
                      />
                    ) : null}
                    <input
                      aria-label={`Stain note on ${itemType.name} ${index + 1}`}
                      className="mt-2 min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                      maxLength="300"
                      placeholder="Describe any serious stain"
                      value={exception.stain_note}
                      disabled={disabled}
                      onChange={(event) => updateTallyException(
                        itemType.id,
                        exception.localId,
                        "stain_note",
                        event.target.value,
                      )}
                    />
                  </div>
                ))}
              </article>
            );
          })}
        </div>

        {onAddMissingItem ? (
          <div className="mt-4 border-t border-blue-200 pt-4">
            {showMissingItemForm ? (
              <form
                className="rounded-xl border border-blue-200 bg-white p-4"
                onSubmit={addMissingTallyItem}
                noValidate
              >
                <label
                  className="block text-sm font-bold text-slate-800"
                  htmlFor={`${fieldPrefix}-missing-tally-item`}
                >
                  Missing clothing item
                </label>
                <p className="mt-1 text-sm text-slate-600">
                  This will become available in every Laundry tally.
                </p>
                <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                  <input
                    className="min-h-11 min-w-0 flex-1 rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                    id={`${fieldPrefix}-missing-tally-item`}
                    maxLength="100"
                    placeholder="Example: School skirt"
                    value={missingItemName}
                    disabled={disabled || isAddingMissingItem}
                    onChange={(event) => {
                      setMissingItemName(event.target.value);
                      setMissingItemFeedback(null);
                    }}
                    autoFocus
                  />
                  <button
                    className="min-h-11 rounded-lg bg-[#005AAB] px-4 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-50"
                    type="submit"
                    disabled={disabled || isAddingMissingItem}
                  >
                    {isAddingMissingItem ? "Adding…" : "Add and count 1"}
                  </button>
                  <button
                    className="min-h-11 rounded-lg border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    type="button"
                    disabled={disabled || isAddingMissingItem}
                    onClick={() => {
                      setShowMissingItemForm(false);
                      setMissingItemName("");
                      setMissingItemFeedback(null);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                className="min-h-11 rounded-lg border border-dashed border-[#005AAB] bg-white px-4 text-sm font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-50"
                type="button"
                disabled={disabled}
                onClick={() => {
                  setShowMissingItemForm(true);
                  setMissingItemFeedback(null);
                }}
              >
                + Add missing clothing item
              </button>
            )}

            {missingItemFeedback ? (
              <p
                className={`mt-3 rounded-lg border px-3 py-2 text-sm font-semibold ${
                  missingItemFeedback.type === "success"
                    ? "border-green-200 bg-green-50 text-green-800"
                    : "border-red-200 bg-red-50 text-red-800"
                }`}
                role={
                  missingItemFeedback.type === "error" ? "alert" : "status"
                }
              >
                {missingItemFeedback.text}
              </p>
            ) : null}
          </div>
        ) : null}
      </section>
    );
  }

  if (recordingMode === "detailed") {
    return (
      <section className="mt-5 rounded-xl border border-blue-200 bg-blue-50 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4 className="font-bold text-slate-900">Garment details</h4>
            <p className="mt-1 text-sm text-slate-600">
              Add each garment separately so its condition and stains stay clear.
            </p>
            <p className="mt-1 text-sm font-semibold text-[#005AAB]">
              {items.length} physical {items.length === 1 ? "piece" : "pieces"} recorded
            </p>
          </div>
          <button
            className="min-h-10 rounded-lg border border-[#005AAB] bg-white px-4 text-sm font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-50"
            type="button"
            disabled={disabled}
            onClick={addGarment}
          >
            Add garment
          </button>
        </div>

        {items.length === 0 ? (
          <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Add at least one garment for this service.
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            {items.map((item, index) => (
              <article
                className="rounded-xl border border-blue-100 bg-white p-4"
                key={item.localId}
              >
                <div className="flex items-center justify-between gap-3">
                  <h5 className="font-bold text-slate-900">
                    {item.garment_reference || `New garment ${index + 1}`}
                  </h5>
                  <button
                    className="text-sm font-bold text-red-700 hover:underline disabled:opacity-50"
                    type="button"
                    disabled={disabled}
                    onClick={() => removeGarment(item.localId)}
                  >
                    Remove
                  </button>
                </div>

                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {fixedItemType ? (
                    <div>
                      <p className="block text-sm font-semibold text-slate-800">
                        Garment
                      </p>
                      <p className="mt-2 flex min-h-11 items-center rounded-lg border border-blue-200 bg-blue-50 px-3 font-bold text-[#005AAB]">
                        {fixedItemType.name}
                      </p>
                    </div>
                  ) : (
                    <div>
                      <label
                        className="block text-sm font-semibold text-slate-800"
                        htmlFor={`${fieldPrefix}-garment-type-${item.localId}`}
                      >
                        Clothing type
                      </label>
                      <select
                        className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                        id={`${fieldPrefix}-garment-type-${item.localId}`}
                        value={item.item_type_id}
                        disabled={disabled}
                        onChange={(event) =>
                          updateGarment(
                            item.localId,
                            "item_type_id",
                            event.target.value,
                          )
                        }
                      >
                        <option value="">Select clothing type</option>
                        {visibleItemTypes.map((itemType) => (
                          <option key={itemType.id} value={itemType.id}>
                            {itemType.name}
                            {itemType.is_active === false ? " (inactive)" : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div>
                    <label
                      className="block text-sm font-semibold text-slate-800"
                      htmlFor={`${fieldPrefix}-garment-damaged-${item.localId}`}
                    >
                      Already damaged?
                    </label>
                    <select
                      className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                      id={`${fieldPrefix}-garment-damaged-${item.localId}`}
                      value={item.is_damaged}
                      disabled={disabled}
                      onChange={(event) =>
                        updateGarment(
                          item.localId,
                          "is_damaged",
                          event.target.value,
                        )
                      }
                    >
                      <option value="">Select Yes or No</option>
                      <option value="false">No</option>
                      <option value="true">Yes</option>
                    </select>
                  </div>
                </div>

                <label
                  className="mt-4 block text-sm font-semibold text-slate-800"
                  htmlFor={`${fieldPrefix}-garment-description-${item.localId}`}
                >
                  Garment description <span aria-hidden="true">*</span>
                </label>
                <input
                  className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                  id={`${fieldPrefix}-garment-description-${item.localId}`}
                  maxLength="200"
                  placeholder="Example: Navy long-sleeved shirt"
                  value={item.description}
                  disabled={disabled}
                  required
                  onChange={(event) =>
                    updateGarment(
                      item.localId,
                      "description",
                      event.target.value,
                    )
                  }
                />

                {item.is_damaged === "true" ? (
                  <>
                    <label
                      className="mt-4 block text-sm font-semibold text-slate-800"
                      htmlFor={`${fieldPrefix}-garment-damage-${item.localId}`}
                    >
                      Existing damage note
                    </label>
                    <input
                      className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                      id={`${fieldPrefix}-garment-damage-${item.localId}`}
                      maxLength="300"
                      placeholder="Example: Small tear near the pocket"
                      value={item.damage_note}
                      disabled={disabled}
                      onChange={(event) =>
                        updateGarment(
                          item.localId,
                          "damage_note",
                          event.target.value,
                        )
                      }
                    />
                  </>
                ) : null}

                <label
                  className="mt-4 block text-sm font-semibold text-slate-800"
                  htmlFor={`${fieldPrefix}-garment-stain-${item.localId}`}
                >
                  Stain or customer note
                </label>
                <input
                  className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                  id={`${fieldPrefix}-garment-stain-${item.localId}`}
                  maxLength="300"
                  placeholder="Example: Ink stain on left sleeve"
                  value={item.stain_note}
                  disabled={disabled}
                  onChange={(event) =>
                    updateGarment(
                      item.localId,
                      "stain_note",
                      event.target.value,
                    )
                  }
                />
              </article>
            ))}
          </div>
        )}
      </section>
    );
  }

  return null;
}
