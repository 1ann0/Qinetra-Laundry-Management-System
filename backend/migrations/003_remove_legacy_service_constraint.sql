-- Removes the old hardcoded service list from the orders table.
-- Detailed orders now validate services against the active catalogue instead.

ALTER TABLE orders
DROP CONSTRAINT IF EXISTS orders_service_type_check;
