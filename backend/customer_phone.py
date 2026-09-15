"""Kenyan customer-phone rules shared by intake, search and later M-PESA prompts."""

import re


ALLOWED_SEPARATORS = re.compile(r"[\s().-]")


def normalize_kenyan_phone(value: str) -> str:
    """Return one database-safe 254XXXXXXXXX form for a Kenyan mobile number."""
    raw_value = str(value or "").strip()
    if not raw_value:
        raise ValueError("Enter the customer's phone number")

    if raw_value.startswith("+"):
        raw_value = raw_value[1:]
    compact = ALLOWED_SEPARATORS.sub("", raw_value)
    if not compact.isdigit():
        raise ValueError("Use numbers, spaces or dashes only")

    if len(compact) == 10 and compact.startswith(("01", "07")):
        compact = f"254{compact[1:]}"
    elif len(compact) == 9 and compact.startswith(("1", "7")):
        compact = f"254{compact}"

    if len(compact) != 12 or not compact.startswith(("2541", "2547")):
        raise ValueError("Enter a Kenyan mobile number such as 0712 345 678")
    return compact


def display_kenyan_phone(value: str) -> str:
    """Show a canonical number in the familiar local format used at the counter."""
    canonical = normalize_kenyan_phone(value)
    return f"0{canonical[3:]}"


def phone_search_digits(value: str) -> str:
    """Return canonical partial digits without rejecting a name search."""
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    if raw_value.startswith("+"):
        raw_value = raw_value[1:]
    compact = ALLOWED_SEPARATORS.sub("", raw_value)
    if not compact.isdigit():
        return ""
    if compact.startswith(("01", "07")):
        return f"254{compact[1:]}"
    if compact.startswith(("1", "7")):
        return f"254{compact}"
    return compact
