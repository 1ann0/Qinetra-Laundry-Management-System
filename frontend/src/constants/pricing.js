export const SERVICES = [
  {
    code: "wash_fold",
    label: "Wash & Fold",
    unit: "kg",
    unitPrice: 150,
  },
  {
    code: "duvet",
    label: "Duvet",
    unit: "piece",
    unitPrice: 800,
  },
  {
    code: "dry_cleaning_shirt",
    label: "Dry Cleaning — Shirt",
    unit: "item",
    unitPrice: 350,
  },
  {
    code: "dry_cleaning_trouser",
    label: "Dry Cleaning — Trouser",
    unit: "item",
    unitPrice: 350,
  },
  {
    code: "dry_cleaning_suit",
    label: "Dry Cleaning — 2-piece Suit",
    unit: "item",
    unitPrice: 750,
  },
];

export const SERVICES_BY_CODE = Object.fromEntries(
  SERVICES.map((service) => [service.code, service]),
);
