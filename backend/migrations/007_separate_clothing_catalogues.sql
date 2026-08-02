-- Separates quick-tally items from Dry Cleaning garments without changing old receipts.
-- Run after 006_add_promised_ready_times.sql and back up Supabase first.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'clothing_item_types'
        AND column_name = 'item_group'
    ) THEN
        ALTER TABLE clothing_item_types
        ADD COLUMN item_group VARCHAR(20) NOT NULL DEFAULT 'laundry';

        -- A garment linked to a Dry Cleaning price belongs in that catalogue.
        UPDATE clothing_item_types
        SET item_group = 'dry_cleaning'
        WHERE id IN (
            SELECT default_item_type_id
            FROM services
            WHERE category = 'dry_cleaning'
            AND default_item_type_id IS NOT NULL
        );

        -- These original tally items are also sold as Dry Cleaning garments.
        UPDATE clothing_item_types
        SET item_group = 'both'
        WHERE name IN ('Shirt', 'T-shirt', 'Trouser', 'Blouse')
        AND id IN (
            SELECT default_item_type_id
            FROM services
            WHERE category = 'dry_cleaning'
            AND default_item_type_id IS NOT NULL
        );

        -- Suit Bag is a Dry Cleaning add-on but is not linked as a garment.
        UPDATE clothing_item_types
        SET item_group = 'dry_cleaning'
        WHERE name = 'Suit Bag';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'clothing_item_types_group_check'
    ) THEN
        ALTER TABLE clothing_item_types
        ADD CONSTRAINT clothing_item_types_group_check
        CHECK (item_group IN ('laundry', 'dry_cleaning', 'both'));
    END IF;
END $$;
