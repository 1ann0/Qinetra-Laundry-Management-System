"use client";

import { useEffect, useRef, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";

const UNIT_OPTIONS = [
  { value: "kg", label: "Per kilogram" },
  { value: "item", label: "Per item" },
  { value: "pair", label: "Per pair" },
];

const RECORDING_MODE_OPTIONS = [
  { value: "none", label: "No clothing list" },
  { value: "tally", label: "Quick tally" },
  { value: "detailed", label: "Individual garment details" },
];

const SERVICE_CATEGORY_OPTIONS = [
  { value: "general", label: "Laundry service" },
  { value: "dry_cleaning", label: "Dry Cleaning garment" },
];
const SUIT_BAG_CODE = "dry_cleaning_suit_bag";

// Keep catalogue entries in alphabetical order after adding or editing them.
function sortByName(items) {
  return [...items].sort((first, second) => first.name.localeCompare(second.name));
}

// Turn the saved recording value into wording the owner can recognise.
function getRecordingModeLabel(mode) {
  return (
    RECORDING_MODE_OPTIONS.find((option) => option.value === mode)?.label ||
    "No clothing list"
  );
}

// Keep validation and success messages beside the action that produced them.
function ActionFeedback({ feedback }) {
  if (!feedback) {
    return null;
  }

  const isError = feedback.type === "error";
  return (
    <p
      className={`mt-4 rounded-xl border px-4 py-3 text-sm ${
        isError
          ? "border-red-300 bg-red-50 text-red-800"
          : "border-green-300 bg-green-50 text-green-800"
      }`}
      role={isError ? "alert" : "status"}
    >
      {feedback.text}
    </p>
  );
}

// Display service prices in a familiar Kenya shilling format.
function formatKes(value) {
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    maximumFractionDigits: 0,
  }).format(value);
}

function ShopSetupContent() {
  const { authenticatedRequest } = useAuth();
  const serviceFormRef = useRef(null);

  // Store both catalogues, including inactive entries needed by the owner.
  const [services, setServices] = useState([]);
  const [itemTypes, setItemTypes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Use the same service form for adding a new service or editing one.
  const [editingServiceId, setEditingServiceId] = useState(null);
  const [editingServiceCode, setEditingServiceCode] = useState("");
  const [serviceName, setServiceName] = useState("");
  const [serviceCategory, setServiceCategory] = useState("general");
  const [serviceItemTypeId, setServiceItemTypeId] = useState("");
  const [serviceUnit, setServiceUnit] = useState("item");
  const [servicePrice, setServicePrice] = useState("");
  const [serviceRecordingMode, setServiceRecordingMode] = useState("none");

  // Use one small form for adding or renaming a clothing item.
  const [editingItemId, setEditingItemId] = useState(null);
  const [itemName, setItemName] = useState("");

  // Give the owner clear feedback while an action is being saved.
  const [busyAction, setBusyAction] = useState("");
  const [pageError, setPageError] = useState("");
  const [serviceFormFeedback, setServiceFormFeedback] = useState(null);
  const [serviceActionFeedback, setServiceActionFeedback] = useState(null);
  const [itemFormFeedback, setItemFormFeedback] = useState(null);
  const [itemActionFeedback, setItemActionFeedback] = useState(null);

  // Load active and inactive entries so the owner can reactivate old choices.
  useEffect(() => {
    async function loadCatalogues() {
      try {
        const [serviceResponse, itemResponse] = await Promise.all([
          authenticatedRequest("/catalog/services?include_inactive=true"),
          authenticatedRequest("/catalog/item-types?include_inactive=true"),
        ]);

        setServices(sortByName(serviceResponse));
        setItemTypes(sortByName(itemResponse));
      } catch (loadError) {
        setPageError(
          loadError.message || "The shop catalogue could not be loaded.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadCatalogues();
  }, [authenticatedRequest]);

  // Return the service form to its normal add-service state.
  function resetServiceForm() {
    setEditingServiceId(null);
    setEditingServiceCode("");
    setServiceName("");
    setServiceCategory("general");
    setServiceItemTypeId("");
    setServiceUnit("item");
    setServicePrice("");
    setServiceRecordingMode("none");
    setServiceFormFeedback(null);
  }

  // Place an existing service in the form so the owner can change it.
  function startServiceEdit(service) {
    setEditingServiceId(service.id);
    setEditingServiceCode(service.code);
    setServiceName(service.name);
    setServiceCategory(service.category || "general");
    setServiceItemTypeId(
      service.default_item_type_id
        ? String(service.default_item_type_id)
        : "",
    );
    setServiceUnit(service.unit);
    setServicePrice(String(service.unit_price));
    setServiceRecordingMode(service.item_recording_mode || "none");
    setServiceFormFeedback(null);
    setServiceActionFeedback(null);

    // Move the form into view because the selected service may be far down the list.
    window.requestAnimationFrame(() => {
      serviceFormRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  // Add a service or save changes to the selected service.
  async function handleServiceSubmit(event) {
    event.preventDefault();
    setServiceFormFeedback(null);

    const cleanedName = serviceName.trim();
    const numericPrice = Number(servicePrice);
    const isSuitBag = editingServiceCode === SUIT_BAG_CODE;
    const savedUnit = serviceCategory === "dry_cleaning" ? "item" : serviceUnit;
    const savedRecordingMode = isSuitBag
      ? "none"
      : serviceCategory === "dry_cleaning"
        ? "detailed"
        : serviceRecordingMode;
    const linkedItemTypeId =
      serviceCategory === "dry_cleaning" && !isSuitBag
        ? Number(serviceItemTypeId)
        : null;

    if (!cleanedName) {
      setServiceFormFeedback({
        type: "error",
        text: "Enter a service name.",
      });
      return;
    }

    if (!Number.isFinite(numericPrice) || numericPrice <= 0) {
      setServiceFormFeedback({
        type: "error",
        text: "Enter a service price greater than zero.",
      });
      return;
    }

    if (
      serviceCategory === "dry_cleaning" &&
      !isSuitBag &&
      !linkedItemTypeId
    ) {
      setServiceFormFeedback({
        type: "error",
        text: "Select the garment this Dry Cleaning price is for.",
      });
      return;
    }

    if (savedRecordingMode === "detailed" && savedUnit === "kg") {
      setServiceFormFeedback({
        type: "error",
        text: "Individual garment details must use per item or per pair pricing.",
      });
      return;
    }

    setBusyAction("service-form");

    try {
      const isEditing = editingServiceId !== null;
      const savedService = await authenticatedRequest(
        isEditing
          ? `/catalog/services/${editingServiceId}`
          : "/catalog/services",
        {
          method: isEditing ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: cleanedName,
            unit: savedUnit,
            unit_price: numericPrice,
            category: serviceCategory,
            default_item_type_id: linkedItemTypeId,
            item_recording_mode: savedRecordingMode,
          }),
        },
      );

      setServices((currentServices) =>
        sortByName(
          isEditing
            ? currentServices.map((service) =>
                service.id === savedService.id ? savedService : service,
              )
            : [...currentServices, savedService],
        ),
      );
      resetServiceForm();
      setServiceFormFeedback({
        type: "success",
        text: isEditing ? "Service changes saved." : "New service added.",
      });
    } catch (saveError) {
      setServiceFormFeedback({
        type: "error",
        text: saveError.message || "The service could not be saved.",
      });
    } finally {
      setBusyAction("");
    }
  }

  // Hide or restore a service without deleting its older records.
  async function toggleService(service) {
    setBusyAction(`service-${service.id}`);
    setServiceActionFeedback(null);

    try {
      const updatedService = await authenticatedRequest(
        `/catalog/services/${service.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !service.is_active }),
        },
      );

      setServices((currentServices) =>
        sortByName(
          currentServices.map((currentService) =>
            currentService.id === updatedService.id
              ? updatedService
              : currentService,
          ),
        ),
      );
      setServiceActionFeedback({
        targetId: service.id,
        type: "success",
        text: updatedService.is_active
          ? `${updatedService.name} is available again.`
          : `${updatedService.name} will not appear in new orders.`,
      });
    } catch (updateError) {
      setServiceActionFeedback({
        targetId: service.id,
        type: "error",
        text:
          updateError.message || "The service status could not be changed.",
      });
    } finally {
      setBusyAction("");
    }
  }

  // Return the clothing-item form to its add-item state.
  function resetItemForm() {
    setEditingItemId(null);
    setItemName("");
    setItemFormFeedback(null);
  }

  // Place an existing clothing item name in the form for editing.
  function startItemEdit(itemType) {
    setEditingItemId(itemType.id);
    setItemName(itemType.name);
    setItemFormFeedback(null);
    setItemActionFeedback(null);
  }

  // Add a clothing name or save a change to the selected one.
  async function handleItemSubmit(event) {
    event.preventDefault();
    setItemFormFeedback(null);

    const cleanedName = itemName.trim();
    if (!cleanedName) {
      setItemFormFeedback({
        type: "error",
        text: "Enter a clothing item name.",
      });
      return;
    }

    setBusyAction("item-form");

    try {
      const isEditing = editingItemId !== null;
      const savedItem = await authenticatedRequest(
        isEditing
          ? `/catalog/item-types/${editingItemId}`
          : "/catalog/item-types",
        {
          method: isEditing ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: cleanedName }),
        },
      );

      setItemTypes((currentItems) =>
        sortByName(
          isEditing
            ? currentItems.map((item) =>
                item.id === savedItem.id ? savedItem : item,
              )
            : [...currentItems, savedItem],
        ),
      );
      resetItemForm();
      setItemFormFeedback({
        type: "success",
        text: isEditing ? "Clothing item updated." : "Clothing item added.",
      });
    } catch (saveError) {
      setItemFormFeedback({
        type: "error",
        text: saveError.message || "The clothing item could not be saved.",
      });
    } finally {
      setBusyAction("");
    }
  }

  // Hide or restore a clothing item without removing its history.
  async function toggleItemType(itemType) {
    setBusyAction(`item-${itemType.id}`);
    setItemActionFeedback(null);

    try {
      const updatedItem = await authenticatedRequest(
        `/catalog/item-types/${itemType.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !itemType.is_active }),
        },
      );

      setItemTypes((currentItems) =>
        sortByName(
          currentItems.map((item) =>
            item.id === updatedItem.id ? updatedItem : item,
          ),
        ),
      );
      setItemActionFeedback({
        targetId: itemType.id,
        type: "success",
        text: updatedItem.is_active
          ? `${updatedItem.name} is available again.`
          : `${updatedItem.name} will not appear in the item tally.`,
      });
    } catch (updateError) {
      setItemActionFeedback({
        targetId: itemType.id,
        type: "error",
        text:
          updateError.message ||
          "The clothing item status could not be changed.",
      });
    } finally {
      setBusyAction("");
    }
  }

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Owner settings
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Shop setup
        </h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">
          Manage the services Qinetra offers and the clothing names employees
          will use when recording a customer&apos;s items.
        </p>
      </div>

      {pageError ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {pageError}
        </p>
      ) : null}

      {isLoading ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600">
          Loading shop setup…
        </p>
      ) : (
        <div className="grid gap-8 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-2xl font-bold text-slate-900">
              Laundry services
            </h2>
            <p className="mt-2 leading-6 text-slate-600">
              Prices changed here apply to future orders. Deactivate a service
              when Qinetra stops offering it.
            </p>

            <form
              className="mt-6 scroll-mt-6 rounded-xl bg-slate-50 p-4"
              onSubmit={handleServiceSubmit}
              ref={serviceFormRef}
            >
              <h3 className="font-bold text-slate-900">
                {editingServiceId ? "Edit service" : "Add a service"}
              </h3>

              <label
                className="mt-4 block font-semibold text-slate-800"
                htmlFor="service-category"
              >
                Service category
              </label>
              <select
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100"
                id="service-category"
                value={serviceCategory}
                disabled={editingServiceCode === SUIT_BAG_CODE}
                onChange={(event) => {
                  const nextCategory = event.target.value;
                  setServiceCategory(nextCategory);
                  setServiceItemTypeId("");
                  if (nextCategory === "dry_cleaning") {
                    setServiceUnit("item");
                    setServiceRecordingMode("detailed");
                  }
                  setServiceFormFeedback(null);
                }}
              >
                {SERVICE_CATEGORY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              <label
                className="mt-4 block font-semibold text-slate-800"
                htmlFor="service-name"
              >
                {serviceCategory === "dry_cleaning"
                  ? "Garment/service name"
                  : "Service name"}
              </label>
              <input
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                id="service-name"
                maxLength="100"
                value={serviceName}
                onChange={(event) => setServiceName(event.target.value)}
              />

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label
                    className="block font-semibold text-slate-800"
                    htmlFor="service-unit"
                  >
                    Charge unit
                  </label>
                  <select
                    className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                    id="service-unit"
                    value={serviceUnit}
                    disabled={serviceCategory === "dry_cleaning"}
                    onChange={(event) => setServiceUnit(event.target.value)}
                  >
                    {UNIT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block font-semibold text-slate-800"
                    htmlFor="service-price"
                  >
                    Price in KES
                  </label>
                  <input
                    className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                    id="service-price"
                    min="1"
                    step="1"
                    type="number"
                    value={servicePrice}
                    onChange={(event) => setServicePrice(event.target.value)}
                  />
                </div>
              </div>

              {serviceCategory === "dry_cleaning" &&
              editingServiceCode !== SUIT_BAG_CODE ? (
                <>
                  <label
                    className="mt-4 block font-semibold text-slate-800"
                    htmlFor="service-item-type"
                  >
                    Garment linked to this price
                  </label>
                  <select
                    className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                    id="service-item-type"
                    value={serviceItemTypeId}
                    onChange={(event) =>
                      setServiceItemTypeId(event.target.value)
                    }
                  >
                    <option value="">Select a garment</option>
                    {itemTypes
                      .filter(
                        (itemType) =>
                          itemType.is_active ||
                          itemType.id === Number(serviceItemTypeId),
                      )
                      .map((itemType) => (
                        <option key={itemType.id} value={itemType.id}>
                          {itemType.name}
                          {itemType.is_active ? "" : " (inactive)"}
                        </option>
                      ))}
                  </select>
                  <p className="mt-2 text-sm leading-5 text-slate-500">
                    Employees will select this garment once, then only record
                    its colour, condition and stain notes.
                  </p>
                </>
              ) : serviceCategory === "dry_cleaning" ? (
                <p className="mt-4 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-slate-700">
                  The suit bag is an optional Dry Cleaning add-on and does not
                  require garment condition details.
                </p>
              ) : (
                <>
                  <label
                    className="mt-4 block font-semibold text-slate-800"
                    htmlFor="service-recording-mode"
                  >
                    How are items recorded?
                  </label>
                  <select
                    className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                    id="service-recording-mode"
                    value={serviceRecordingMode}
                    onChange={(event) =>
                      setServiceRecordingMode(event.target.value)
                    }
                  >
                    {RECORDING_MODE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="mt-2 text-sm leading-5 text-slate-500">
                    Quick tally counts clothing pieces. Individual details
                    record each garment, its condition and stain notes.
                  </p>
                </>
              )}

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  className="min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
                  type="submit"
                  disabled={Boolean(busyAction)}
                >
                  {busyAction === "service-form"
                    ? "Saving…"
                    : editingServiceId
                      ? "Save changes"
                      : "Add service"}
                </button>
                {editingServiceId ? (
                  <button
                    className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-white"
                    type="button"
                    onClick={resetServiceForm}
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
              <ActionFeedback feedback={serviceFormFeedback} />
            </form>

            <div className="mt-6 space-y-3">
              {services.map((service) => (
                <article
                  className={`rounded-xl border p-4 ${
                    service.is_active
                      ? "border-slate-200"
                      : "border-slate-200 bg-slate-50"
                  }`}
                  key={service.id}
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-bold text-slate-900">{service.name}</h3>
                        <span
                          className={`rounded-full px-2 py-1 text-xs font-bold ${
                            service.is_active
                              ? "bg-green-100 text-green-800"
                              : "bg-slate-200 text-slate-700"
                          }`}
                        >
                          {service.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">
                        {formatKes(service.unit_price)} per {service.unit}
                      </p>
                      <p className="mt-1 text-sm font-semibold text-[#005AAB]">
                        {getRecordingModeLabel(service.item_recording_mode)}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        className="font-bold text-[#005AAB] hover:underline disabled:opacity-50"
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={() => startServiceEdit(service)}
                      >
                        Edit
                      </button>
                      <button
                        className="font-bold text-slate-700 hover:underline disabled:opacity-50"
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={() => toggleService(service)}
                      >
                        {busyAction === `service-${service.id}`
                          ? "Saving…"
                          : service.is_active
                            ? "Deactivate"
                            : "Reactivate"}
                      </button>
                    </div>
                  </div>
                  <ActionFeedback
                    feedback={
                      serviceActionFeedback?.targetId === service.id
                        ? serviceActionFeedback
                        : null
                    }
                  />
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-2xl font-bold text-slate-900">
              Clothing item names
            </h2>
            <p className="mt-2 leading-6 text-slate-600">
              These names will become the quick tally choices employees use
              while checking a customer&apos;s laundry.
            </p>

            <form
              className="mt-6 rounded-xl bg-slate-50 p-4"
              onSubmit={handleItemSubmit}
            >
              <h3 className="font-bold text-slate-900">
                {editingItemId ? "Edit clothing item" : "Add a clothing item"}
              </h3>

              <label
                className="mt-4 block font-semibold text-slate-800"
                htmlFor="item-name"
              >
                Clothing item name
              </label>
              <input
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                id="item-name"
                maxLength="100"
                value={itemName}
                onChange={(event) => setItemName(event.target.value)}
              />

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  className="min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
                  type="submit"
                  disabled={Boolean(busyAction)}
                >
                  {busyAction === "item-form"
                    ? "Saving…"
                    : editingItemId
                      ? "Save changes"
                      : "Add clothing item"}
                </button>
                {editingItemId ? (
                  <button
                    className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-white"
                    type="button"
                    onClick={resetItemForm}
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
              <ActionFeedback feedback={itemFormFeedback} />
            </form>

            <div className="mt-6 space-y-3">
              {itemTypes.map((itemType) => (
                <article
                  className={`rounded-xl border p-4 ${
                    itemType.is_active
                      ? "border-slate-200"
                      : "border-slate-200 bg-slate-50"
                  }`}
                  key={itemType.id}
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-bold text-slate-900">{itemType.name}</h3>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-bold ${
                          itemType.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {itemType.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        className="font-bold text-[#005AAB] hover:underline disabled:opacity-50"
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={() => startItemEdit(itemType)}
                      >
                        Edit
                      </button>
                      <button
                        className="font-bold text-slate-700 hover:underline disabled:opacity-50"
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={() => toggleItemType(itemType)}
                      >
                        {busyAction === `item-${itemType.id}`
                          ? "Saving…"
                          : itemType.is_active
                            ? "Deactivate"
                            : "Reactivate"}
                      </button>
                    </div>
                  </div>
                  <ActionFeedback
                    feedback={
                      itemActionFeedback?.targetId === itemType.id
                        ? itemActionFeedback
                        : null
                    }
                  />
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

export default function ShopSetupPage() {
  return (
    <OwnerGuard>
      <ShopSetupContent />
    </OwnerGuard>
  );
}
