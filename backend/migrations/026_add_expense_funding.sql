-- No source is guessed for old expenses; their immutable events stay untouched.
BEGIN;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS funding_source VARCHAR(10)
    CONSTRAINT expense_funding_source CHECK (funding_source IN ('shop', 'owner'));
COMMIT;
