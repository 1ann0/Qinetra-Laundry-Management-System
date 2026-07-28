-- Adds append-only payment history for Cash, M-PESA and deposits.
-- Run after the mixed-order migrations and back up Supabase first.

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    payment_method VARCHAR(20) NOT NULL
        CHECK (payment_method IN ('cash', 'mpesa', 'legacy')),
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    confirmed_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    confirmed_by_username VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS payments_order_id_idx
ON payments(order_id);

-- A collected order must have been paid under the old paper/Excel workflow.
-- This avoids incorrectly listing completed historical work as unpaid.
INSERT INTO payments (
    order_id,
    payment_method,
    amount,
    confirmed_by_id,
    confirmed_by_username
)
SELECT
    orders.id,
    'legacy',
    orders.total_price,
    NULL,
    'Recorded before payment tracking'
FROM orders
WHERE orders.status = 'collected'
AND NOT EXISTS (
    SELECT 1
    FROM payments
    WHERE payments.order_id = orders.id
);
