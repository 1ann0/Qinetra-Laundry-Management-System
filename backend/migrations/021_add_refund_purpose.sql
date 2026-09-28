-- Explicit purposes for new refunds; older events retain their existing meaning.
BEGIN;
ALTER TABLE payment_adjustments ADD COLUMN IF NOT EXISTS refund_purpose VARCHAR(20);
ALTER TABLE payment_adjustments DROP CONSTRAINT IF EXISTS payment_adjustment_refund_purpose;
ALTER TABLE payment_adjustments ADD CONSTRAINT payment_adjustment_refund_purpose CHECK (
    refund_purpose IS NULL OR
    (kind = 'refund' AND refund_purpose IN ('service_refund', 'excess_payment'))
);
-- Existing RLS and role grants remain in force; this adds no public access.
COMMIT;
