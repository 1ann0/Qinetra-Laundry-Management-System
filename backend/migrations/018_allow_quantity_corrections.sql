-- Expand the existing owner correction history to include billed quantity fixes.
BEGIN;

ALTER TABLE order_corrections DROP CONSTRAINT IF EXISTS order_correction_action;
ALTER TABLE order_corrections ADD CONSTRAINT order_correction_action
CHECK (action IN ('stage_back', 'cancel', 'quantity'));

COMMIT;
