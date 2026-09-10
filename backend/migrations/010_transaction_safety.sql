-- Apply before releasing the matching API and frontend. Keeps historical records intact.
BEGIN;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS request_key VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS request_hash VARCHAR(64);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
CREATE UNIQUE INDEX IF NOT EXISTS orders_request_key_key ON orders(request_key);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS request_key VARCHAR(36);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS request_hash VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS payments_request_key_key ON payments(request_key);
ALTER TABLE order_service_lines ADD COLUMN IF NOT EXISTS item_revision INTEGER NOT NULL DEFAULT 0;

-- Each date has one counter row; the API seeds it from the highest existing ticket.
CREATE TABLE IF NOT EXISTS ticket_counters (
    ticket_date DATE PRIMARY KEY,
    last_number INTEGER NOT NULL
);
ALTER TABLE ticket_counters ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ticket_counters FROM PUBLIC;
-- These roles exist on Supabase, but need not exist on a local PostgreSQL server.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON ticket_counters FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON ticket_counters FROM authenticated;
    END IF;
END $$;
COMMIT;
