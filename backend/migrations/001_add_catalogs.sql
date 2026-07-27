-- Adds owner-managed services and clothing item types.
-- Review and back up Supabase before running this file in the SQL Editor.

CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    unit VARCHAR(20) NOT NULL CHECK (unit IN ('kg', 'item', 'pair')),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clothing_item_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed the prices already used by the existing QLMS order calculator.
INSERT INTO services (code, name, unit, unit_price)
VALUES
    ('wash_fold', 'Wash & Fold', 'kg', 150),
    ('duvet', 'Duvet Cleaning', 'item', 800),
    ('dry_cleaning_shirt', 'Dry Cleaning - Shirt', 'item', 350),
    ('dry_cleaning_trouser', 'Dry Cleaning - Trouser', 'item', 350),
    ('dry_cleaning_suit', 'Dry Cleaning - 2-piece Suit', 'item', 750)
ON CONFLICT (code) DO NOTHING;

-- Seed the clothing names confirmed during the panel feedback.
INSERT INTO clothing_item_types (name)
VALUES
    ('Shirt'),
    ('T-shirt'),
    ('Trouser'),
    ('Jacket'),
    ('Socks (Pair)'),
    ('Single Sock'),
    ('Underwear'),
    ('Blouse'),
    ('Bedsheet'),
    ('Vest'),
    ('Pillowcase'),
    ('Shorts'),
    ('Bra'),
    ('Towel')
ON CONFLICT (name) DO NOTHING;
