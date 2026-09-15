-- Adds one searchable Kenyan mobile value while preserving the familiar display value.
BEGIN;

ALTER TABLE customers
ADD COLUMN IF NOT EXISTS phone_normalized VARCHAR(12);

WITH cleaned AS (
    SELECT
        id,
        REGEXP_REPLACE(phone, '[^0-9]', '', 'g') AS digits
    FROM customers
)
UPDATE customers
SET phone_normalized = CASE
    WHEN LENGTH(cleaned.digits) = 10 AND cleaned.digits ~ '^0[17]'
        THEN '254' || SUBSTRING(cleaned.digits FROM 2)
    WHEN LENGTH(cleaned.digits) = 9 AND cleaned.digits ~ '^[17]'
        THEN '254' || cleaned.digits
    WHEN LENGTH(cleaned.digits) = 12 AND cleaned.digits ~ '^254[17]'
        THEN cleaned.digits
    ELSE NULL
END
FROM cleaned
WHERE customers.id = cleaned.id
  AND customers.phone_normalized IS NULL;

CREATE INDEX IF NOT EXISTS customers_phone_normalized_idx
ON customers(phone_normalized);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'customers_phone_normalized_format'
          AND conrelid = 'customers'::regclass
    ) THEN
        ALTER TABLE customers
        ADD CONSTRAINT customers_phone_normalized_format
        CHECK (
            phone_normalized IS NULL
            OR phone_normalized ~ '^254[17][0-9]{8}$'
        );
    END IF;
END $$;

COMMIT;
