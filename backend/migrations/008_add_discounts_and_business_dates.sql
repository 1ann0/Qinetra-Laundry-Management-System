-- Adds explicit business dates and per-service discounts without changing catalogue prices.
-- Run after 007_separate_clothing_catalogues.sql and back up Supabase first.

ALTER TABLE order_service_lines
ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_date DATE;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS discount_reason VARCHAR(120);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS discounted_by_username VARCHAR(50);

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS received_date DATE;

-- Preserve the original Nairobi business day for records created before this migration.
UPDATE orders
SET order_date = (created_at AT TIME ZONE 'Africa/Nairobi')::DATE
WHERE order_date IS NULL;

UPDATE payments
SET received_date = (created_at AT TIME ZONE 'Africa/Nairobi')::DATE
WHERE received_date IS NULL;

ALTER TABLE orders
ALTER COLUMN order_date SET NOT NULL;

ALTER TABLE payments
ALTER COLUMN received_date SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'order_service_lines_discount_check'
    ) THEN
        ALTER TABLE order_service_lines
        ADD CONSTRAINT order_service_lines_discount_check
        CHECK (discount_amount >= 0 AND discount_amount < subtotal);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS orders_order_date_idx
ON orders(order_date);

CREATE INDEX IF NOT EXISTS payments_received_date_idx
ON payments(received_date);
