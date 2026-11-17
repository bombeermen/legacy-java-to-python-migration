"""FastAPI wrapper around the migrated billing.py.

Usage:
    python -m uvicorn app:app

Docs and a try-it form: http://127.0.0.1:8000/docs
"""
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import billing

app = FastAPI(title="Invoice API", description="Legacy Java billing, migrated to Python with Claude Haiku")


class ItemIn(BaseModel):
    sku: str
    qty: int
    unit_price: Decimal


class InvoiceIn(BaseModel):
    id: str
    customer_type: str = Field(examples=["RETAIL"], description="RETAIL, WHOLESALE або GOV")
    region: str = Field(examples=["EU"], description="EU, US або UA")
    days_late: int = 0
    items: list[ItemIn]


class InvoiceOut(BaseModel):
    id: str
    subtotal: str
    discount: str
    shipping: str
    tax: str
    late_fee: str
    total: str


@app.post("/invoice", response_model=InvoiceOut)
def calculate_invoice(body: InvoiceIn) -> InvoiceOut:
    invoice = billing.Invoice(body.id, body.customer_type, body.region, body.days_late)
    for item in body.items:
        invoice.add_item(billing.LineItem(item.sku, item.qty, item.unit_price))
    try:
        r = billing.calculate(invoice)
    except billing.InvoiceError as exc:  # same messages the Java program printed (ERROR|...)
        raise HTTPException(status_code=422, detail=str(exc))
    plain = billing._plain  # amounts as strings, no loss of Decimal precision
    return InvoiceOut(
        id=invoice.id,
        subtotal=plain(r.subtotal),
        discount=plain(r.discount),
        shipping=plain(r.shipping),
        tax=plain(r.tax),
        late_fee=plain(r.late_fee),
        total=plain(r.total),
    )
