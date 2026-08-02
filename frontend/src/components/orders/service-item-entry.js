"use client";

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
    item_type_id: itemTypeId,
    description: "",
    is_damaged: "",
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
}) {
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
    const nextQuantity = Math.max(0, (currentItem?.quantity || 0) + amount);
    const otherItems = items.filter(
      (item) => item.item_type_id !== itemTypeId,
    );

    onItemsChange(
      nextQuantity > 0
        ? [...otherItems, { item_type_id: itemTypeId, quantity: nextQuantity }]
        : otherItems,
    );
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
            const quantity =
              items.find((item) => item.item_type_id === itemType.id)
                ?.quantity || 0;

            return (
              <div
                className="flex items-center justify-between gap-3 rounded-lg border border-blue-100 bg-white px-3 py-2"
                key={itemType.id}
              >
                <span className="text-sm font-semibold text-slate-800">
                  {itemType.name}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                    type="button"
                    aria-label={`Remove one ${itemType.name}`}
                    disabled={disabled || quantity === 0}
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
            );
          })}
        </div>
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
                    Garment {index + 1}
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
                  Garment description
                </label>
                <input
                  className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                  id={`${fieldPrefix}-garment-description-${item.localId}`}
                  maxLength="200"
                  placeholder="Example: Navy long-sleeved shirt"
                  value={item.description}
                  disabled={disabled}
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
