-- Add wrong-customer reassignment to the existing order correction history.
BEGIN;

ALTER TABLE order_corrections DROP CONSTRAINT IF EXISTS order_correction_action;
ALTER TABLE order_corrections ADD CONSTRAINT order_correction_action
CHECK (action IN ('stage_back', 'cancel', 'quantity', 'customer_reassign'));

COMMIT;
