"""Apply the owner's whole-order employee ceiling using decimal money."""
from decimal import Decimal, ROUND_DOWN

import models
from transaction_safety import lock_save_reference, reject_unsaved_change


def read_discount_policy(db, *, lock=False):
    # The same transaction lock covers updates and discounted order acceptance,
    # including a fresh database where the singleton has not been seeded yet.
    if lock:
        lock_save_reference(db, "qlms:employee-discount-policy")
    policy = db.query(models.DiscountPolicy).populate_existing().filter_by(id=1).first()
    return policy or models.DiscountPolicy(
        id=1, employee_max_discount_percent=Decimal("0"), revision=0,
    )


def enforce_employee_discount(db, user, subtotal, discount):
    if user.role == "owner" or discount == 0:
        return
    policy = read_discount_policy(db, lock=True)
    # Round the allowance down: rounding up could exceed the agreed percentage.
    allowance = (subtotal * policy.employee_max_discount_percent / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN,
    )
    if discount > allowance:
        raise reject_unsaved_change(
            "QLMS-DISCOUNT-LIMIT", "The whole-order discount exceeds the employee limit",
        )
