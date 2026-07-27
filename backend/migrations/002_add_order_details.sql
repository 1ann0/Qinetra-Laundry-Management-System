-- Adds mixed services and clothing records without changing existing orders.
-- Back up Supabase and run this after 001_add_catalogs.sql.

ALTER TABLE services
ADD COLUMN IF NOT EXISTS item_recording_mode VARCHAR(20) NOT NULL DEFAULT 'none';

-- Give the current services the recording behaviour agreed after panel feedback.
UPDATE services
SET item_recording_mode = CASE
    WHEN code = 'wash_fold' THEN 'tally'
    WHEN code LIKE 'dry\_cleaning\_%' ESCAPE '\' THEN 'detailed'
    ELSE 'none'
END;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'services_item_recording_mode_check'
    ) THEN
        ALTER TABLE services
        ADD CONSTRAINT services_item_recording_mode_check
        CHECK (item_recording_mode IN ('none', 'tally', 'detailed'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS order_service_lines (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES services(id),
    service_name VARCHAR(100) NOT NULL,
    service_unit VARCHAR(20) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price > 0),
    subtotal NUMERIC(10, 2) NOT NULL CHECK (subtotal > 0),
    item_recording_mode VARCHAR(20) NOT NULL
        CHECK (item_recording_mode IN ('none', 'tally', 'detailed')),
    item_check_status VARCHAR(20) NOT NULL DEFAULT 'not_required'
        CHECK (item_check_status IN ('not_required', 'pending', 'completed')),
    UNIQUE (order_id, service_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_service_line_id INTEGER NOT NULL
        REFERENCES order_service_lines(id) ON DELETE CASCADE,
    item_type_id INTEGER NOT NULL REFERENCES clothing_item_types(id),
    item_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    description VARCHAR(200),
    is_damaged BOOLEAN,
    damage_note VARCHAR(300),
    stain_note VARCHAR(300)
);

CREATE INDEX IF NOT EXISTS order_service_lines_order_id_idx
ON order_service_lines(order_id);

CREATE INDEX IF NOT EXISTS order_items_service_line_id_idx
ON order_items(order_service_line_id);
