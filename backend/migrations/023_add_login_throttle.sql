-- Shared login windows; identifiers are keyed hashes, not raw IPs/usernames.
BEGIN;
CREATE TABLE IF NOT EXISTS login_attempt_buckets (
    bucket_key VARCHAR(64) PRIMARY KEY,
    window_start BIGINT NOT NULL,
    attempts INTEGER NOT NULL,
    CONSTRAINT login_attempt_positive CHECK (attempts > 0)
);
CREATE INDEX IF NOT EXISTS ix_login_attempt_buckets_window_start ON login_attempt_buckets(window_start);
ALTER TABLE login_attempt_buckets ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON login_attempt_buckets FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON login_attempt_buckets FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON login_attempt_buckets FROM authenticated;
    END IF;
END $$;
COMMIT;
