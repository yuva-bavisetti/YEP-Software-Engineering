"""Exact quotation/BOQ calculations; monetary storage is integer paise."""

from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException


def fail(code, message):
    raise HTTPException(code, message)


def cents(v):
    return int((Decimal(v) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def quotation_total(d):
    if not d.items:
        if d.tax_percent or d.discount:
            fail(422, "Add BOQ items before applying tax or discount")
        return cents(d.amount)
    subtotal = sum(cents(i.quantity * i.unit_price) for i in d.items)
    total = (
        subtotal
        + int(
            (Decimal(subtotal) * d.tax_percent / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        - cents(d.discount)
    )
    if total <= 0:
        fail(422, "Quotation total must be positive")
    if total != cents(d.amount):
        fail(422, "Amount must match the BOQ total, tax and discount")
    return total
