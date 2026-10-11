"""Exact byte projection for the owner's approved 5 GB backup allowance."""

APPROVED_BUDGET_BYTES = 5000000000


def backup_projection(archive_bytes, retention_days, budget_bytes=APPROVED_BUDGET_BYTES):
    if any(type(value) is not int or value <= 0 for value in (archive_bytes, retention_days, budget_bytes)):
        raise ValueError("Storage projection needs positive whole-byte sizes and retention")
    if budget_bytes > APPROVED_BUDGET_BYTES:
        raise ValueError("Do not exceed the owner's approved storage allowance")
    reserved = budget_bytes // 5
    usable = budget_bytes - reserved
    projected = archive_bytes * retention_days
    if projected > usable:
        raise ValueError("Retained-copy projection exceeds the approved budget with headroom")
    return {"archive_bytes": archive_bytes, "retention_days": retention_days,
            "storage_budget_bytes": budget_bytes, "reserved_bytes": reserved,
            "usable_budget_bytes": usable, "projected_retained_bytes": projected,
            "maximum_daily_bytes": usable // retention_days}
