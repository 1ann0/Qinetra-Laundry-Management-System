-- Groups separately priced garments under Dry Cleaning without changing old receipts.
-- Run after 004_add_payments.sql and back up Supabase first.

ALTER TABLE services
ADD COLUMN IF NOT EXISTS category VARCHAR(30) NOT NULL DEFAULT 'general';

ALTER TABLE services
ADD COLUMN IF NOT EXISTS default_item_type_id INTEGER
REFERENCES clothing_item_types(id) ON DELETE SET NULL;

ALTER TABLE order_service_lines
ADD COLUMN IF NOT EXISTS fixed_item_type_id INTEGER
REFERENCES clothing_item_types(id) ON DELETE SET NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'services_category_check'
    ) THEN
        ALTER TABLE services
        ADD CONSTRAINT services_category_check
        CHECK (category IN ('general', 'dry_cleaning'));
    END IF;
END $$;

-- Add the garment names confirmed during the system review.
INSERT INTO clothing_item_types (name)
VALUES
    ('White T-shirt'),
    ('Polo T-shirt'),
    ('Suit Coat / School Blazer'),
    ('2-Piece Suit'),
    ('3-Piece Suit'),
    ('Hoodie'),
    ('Trench Coat'),
    ('Pillow'),
    ('White/Cream/Coloured Suit Coat'),
    ('Kitenge Dress'),
    ('Kitenge Shirt'),
    ('Kaunda Shirt'),
    ('Sweater'),
    ('Dress'),
    ('Bridesmaid/Sequined Dress'),
    ('Suit Bag')
ON CONFLICT (name) DO NOTHING;

-- Link the three existing Dry Cleaning prices to their fixed garment names.
UPDATE services AS service
SET
    category = 'dry_cleaning',
    item_recording_mode = 'detailed',
    default_item_type_id = item_type.id
FROM (
    VALUES
        ('dry_cleaning_shirt', 'Shirt'),
        ('dry_cleaning_trouser', 'Trouser'),
        ('dry_cleaning_suit', '2-Piece Suit')
) AS mapping(service_code, item_name)
JOIN clothing_item_types AS item_type
    ON item_type.name = mapping.item_name
WHERE service.code = mapping.service_code;

-- Add the remaining garment prices as owner-managed services.
INSERT INTO services (
    code,
    name,
    unit,
    unit_price,
    item_recording_mode,
    category,
    default_item_type_id
)
SELECT
    garment.code,
    garment.service_name,
    'item',
    garment.unit_price,
    'detailed',
    'dry_cleaning',
    item_type.id
FROM (
    VALUES
        ('dry_cleaning_t_shirt', 'Dry Cleaning - T-shirt', 230.00, 'T-shirt'),
        ('dry_cleaning_white_t_shirt', 'Dry Cleaning - White T-shirt', 250.00, 'White T-shirt'),
        ('dry_cleaning_polo_t_shirt', 'Dry Cleaning - Polo T-shirt', 280.00, 'Polo T-shirt'),
        ('dry_cleaning_suit_coat_school_blazer', 'Dry Cleaning - Suit Coat / School Blazer', 450.00, 'Suit Coat / School Blazer'),
        ('dry_cleaning_3_piece_suit', 'Dry Cleaning - 3-Piece Suit', 950.00, '3-Piece Suit'),
        ('dry_cleaning_blouse', 'Dry Cleaning - Blouse', 200.00, 'Blouse'),
        ('dry_cleaning_hoodie', 'Dry Cleaning - Hoodie', 600.00, 'Hoodie'),
        ('dry_cleaning_trench_coat', 'Dry Cleaning - Trench Coat', 750.00, 'Trench Coat'),
        ('dry_cleaning_pillow', 'Dry Cleaning - Pillow', 650.00, 'Pillow'),
        ('dry_cleaning_coloured_suit_coat', 'Dry Cleaning - White/Cream/Coloured Suit Coat', 550.00, 'White/Cream/Coloured Suit Coat'),
        ('dry_cleaning_kitenge_dress', 'Dry Cleaning - Kitenge Dress', 750.00, 'Kitenge Dress'),
        ('dry_cleaning_kitenge_shirt', 'Dry Cleaning - Kitenge Shirt', 550.00, 'Kitenge Shirt'),
        ('dry_cleaning_kaunda_shirt', 'Dry Cleaning - Kaunda Shirt', 550.00, 'Kaunda Shirt'),
        ('dry_cleaning_sweater', 'Dry Cleaning - Sweater', 400.00, 'Sweater'),
        ('dry_cleaning_dress', 'Dry Cleaning - Dress', 450.00, 'Dress'),
        ('dry_cleaning_bridesmaid_sequined_dress', 'Dry Cleaning - Bridesmaid/Sequined Dress', 750.00, 'Bridesmaid/Sequined Dress')
) AS garment(code, service_name, unit_price, item_name)
JOIN clothing_item_types AS item_type
    ON item_type.name = garment.item_name
ON CONFLICT DO NOTHING;

-- Suit bags are an optional add-on and do not need damage or stain details.
INSERT INTO services (
    code,
    name,
    unit,
    unit_price,
    item_recording_mode,
    category,
    default_item_type_id
)
VALUES (
    'dry_cleaning_suit_bag',
    'Dry Cleaning - Suit Bag',
    'item',
    100.00,
    'none',
    'dry_cleaning',
    NULL
)
ON CONFLICT DO NOTHING;

-- Existing detailed order lines keep the garment linked at the time of this change.
UPDATE order_service_lines AS service_line
SET fixed_item_type_id = service.default_item_type_id
FROM services AS service
WHERE service_line.service_id = service.id
AND service_line.fixed_item_type_id IS NULL
AND service.default_item_type_id IS NOT NULL;
