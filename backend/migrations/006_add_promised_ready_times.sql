-- Adds service turnaround settings and the promised completion time saved on each order.
-- Run after 005_group_dry_cleaning_garments.sql and back up Supabase first.

-- Only apply the starting values when this column is first introduced.
-- This avoids overwriting an owner's later changes if the script is run again.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'services'
        AND column_name = 'turnaround_minutes'
    ) THEN
        ALTER TABLE services
        ADD COLUMN turnaround_minutes INTEGER NOT NULL DEFAULT 180;

        -- Qinetra normally completes Dry Cleaning in three calendar days.
        UPDATE services
        SET turnaround_minutes = 4320
        WHERE category = 'dry_cleaning';
    END IF;
END $$;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS promised_ready_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS peak_delay_minutes INTEGER NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'services_turnaround_minutes_check'
    ) THEN
        ALTER TABLE services
        ADD CONSTRAINT services_turnaround_minutes_check
        CHECK (turnaround_minutes > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'orders_peak_delay_minutes_check'
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT orders_peak_delay_minutes_check
        CHECK (peak_delay_minutes IN (0, 60));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS orders_promised_ready_at_idx
ON orders(promised_ready_at);
