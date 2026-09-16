-- Separates physical garment identity from the quantity used for pricing.
BEGIN;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS next_garment_number INTEGER NOT NULL DEFAULT 1;

ALTER TABLE order_items
ADD COLUMN IF NOT EXISTS garment_reference VARCHAR(50);

WITH ranked_garments AS (
    SELECT
        order_items.id,
        orders.ticket_number,
        ROW_NUMBER() OVER (
            PARTITION BY orders.id
            ORDER BY order_service_lines.id, order_items.id
        ) AS garment_number
    FROM order_items
    JOIN order_service_lines
      ON order_service_lines.id = order_items.order_service_line_id
    JOIN orders ON orders.id = order_service_lines.order_id
    WHERE order_service_lines.item_recording_mode = 'detailed'
)
UPDATE order_items
SET garment_reference = ranked_garments.ticket_number
    || '-G' || LPAD(ranked_garments.garment_number::TEXT, 2, '0')
FROM ranked_garments
WHERE order_items.id = ranked_garments.id
  AND order_items.garment_reference IS NULL;

WITH highest_references AS (
    SELECT
        order_service_lines.order_id,
        MAX(
            SUBSTRING(order_items.garment_reference FROM '-G([0-9]+)$')::INTEGER
        ) AS highest_number
    FROM order_items
    JOIN order_service_lines
      ON order_service_lines.id = order_items.order_service_line_id
    WHERE order_items.garment_reference IS NOT NULL
    GROUP BY order_service_lines.order_id
)
UPDATE orders
SET next_garment_number = GREATEST(
    orders.next_garment_number,
    highest_references.highest_number + 1
)
FROM highest_references
WHERE orders.id = highest_references.order_id;

CREATE UNIQUE INDEX IF NOT EXISTS ix_order_items_garment_reference
ON order_items(garment_reference);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'orders_next_garment_number_positive'
          AND conrelid = 'orders'::regclass
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT orders_next_garment_number_positive
        CHECK (next_garment_number > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'order_items_garment_reference_not_blank'
          AND conrelid = 'order_items'::regclass
    ) THEN
        ALTER TABLE order_items
        ADD CONSTRAINT order_items_garment_reference_not_blank
        CHECK (
            garment_reference IS NULL
            OR LENGTH(TRIM(garment_reference)) > 0
        );
    END IF;
END $$;

COMMIT;
