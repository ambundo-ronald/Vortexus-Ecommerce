from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from vortexus_ecommerce_integration.constants import (
    CUSTOM_CHANNEL_FIELD,
    CUSTOM_ORDER_ID_FIELD,
    CUSTOM_ORDER_NUMBER_FIELD,
    CUSTOM_PAYMENT_PROVIDER_FIELD,
    CUSTOM_PAYMENT_REFERENCE_FIELD,
    CUSTOM_SOURCE_FIELD,
    SALES_CHANNEL_VALUE,
    SOURCE_VALUE,
)


@frappe.whitelist()
def create_sales_order(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    order_id = str(payload.get("order_id") or "").strip()
    order_number = str(payload.get("order_number") or order_id).strip()
    if not order_id:
        frappe.throw(_("order_id is required."))

    existing = frappe.db.get_value("Sales Order", {CUSTOM_ORDER_ID_FIELD: order_id}, "name")
    if existing:
        return {"sales_order": existing, "created": False}

    items = _sales_order_items(payload)
    if not items:
        frappe.throw(_("At least one item is required to create an ecommerce Sales Order."))

    doc = frappe.get_doc(
        {
            "doctype": "Sales Order",
            "customer": payload.get("customer"),
            "company": payload.get("company"),
            "transaction_date": getdate(payload.get("transaction_date")) or nowdate(),
            "delivery_date": getdate(payload.get("delivery_date")) or nowdate(),
            "currency": payload.get("currency") or "KES",
            "po_no": order_number,
            "selling_price_list": payload.get("selling_price_list"),
            "ignore_pricing_rule": 1,
            "items": items,
        }
    )
    _tag_ecommerce_doc(doc, payload)
    doc.flags.ignore_permissions = True
    doc.insert(ignore_mandatory=True)
    if payload.get("submit", True):
        doc.submit()
    return {"sales_order": doc.name, "created": True}


@frappe.whitelist()
def create_sales_invoice(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    sales_order = payload.get("sales_order") or _find_sales_order(payload)
    if not sales_order:
        frappe.throw(_("sales_order or order_id is required."))

    existing = frappe.db.get_value("Sales Invoice", {CUSTOM_ORDER_ID_FIELD: payload.get("order_id")}, "name")
    if existing:
        return {"sales_invoice": existing, "created": False}

    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    invoice = make_sales_invoice(sales_order, ignore_permissions=True)
    _tag_ecommerce_doc(invoice, payload)
    invoice.set_posting_time = 1
    invoice.posting_date = getdate(payload.get("posting_date")) or nowdate()
    invoice.due_date = getdate(payload.get("due_date")) or invoice.posting_date
    invoice.flags.ignore_permissions = True
    invoice.insert(ignore_mandatory=True)
    if payload.get("submit", True):
        invoice.submit()

    payment_reference = payload.get("payment_reference")
    payment_entry_name = None
    if payload.get("create_payment_entry") and payment_reference:
        payment_entry_name = create_payment_entry(
            {
                "sales_invoice": invoice.name,
                "order_number": payload.get("order_number"),
                "payment_provider": payload.get("payment_provider"),
                "payment_reference": payment_reference,
                "paid_amount": payload.get("paid_amount") or invoice.grand_total,
                "bank_account": payload.get("bank_account"),
                "posting_date": payload.get("posting_date"),
            }
        ).get("payment_entry")

    return {"sales_invoice": invoice.name, "payment_entry": payment_entry_name, "created": True}


@frappe.whitelist()
def create_payment_entry(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    sales_invoice = payload.get("sales_invoice")
    if not sales_invoice:
        frappe.throw(_("sales_invoice is required."))

    payment_reference = payload.get("payment_reference")
    existing = None
    if payment_reference:
        existing = frappe.db.get_value("Payment Entry", {CUSTOM_PAYMENT_REFERENCE_FIELD: payment_reference}, "name")
    if existing:
        return {"payment_entry": existing, "created": False}

    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    payment = get_payment_entry("Sales Invoice", sales_invoice, bank_account=payload.get("bank_account"))
    payment.paid_amount = flt(payload.get("paid_amount") or payment.paid_amount)
    payment.received_amount = payment.paid_amount
    payment.reference_no = payment_reference or sales_invoice
    payment.reference_date = getdate(payload.get("posting_date")) or nowdate()
    payment.posting_date = payment.reference_date
    payment.set(CUSTOM_SOURCE_FIELD, SOURCE_VALUE)
    payment.set(CUSTOM_ORDER_NUMBER_FIELD, payload.get("order_number"))
    payment.set(CUSTOM_PAYMENT_PROVIDER_FIELD, payload.get("payment_provider"))
    payment.set(CUSTOM_PAYMENT_REFERENCE_FIELD, payment_reference)
    payment.flags.ignore_permissions = True
    payment.insert(ignore_mandatory=True)
    if payload.get("submit", True):
        payment.submit()
    return {"payment_entry": payment.name, "created": True}


@frappe.whitelist()
def cancel_sales_order(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    sales_order = payload.get("sales_order") or _find_sales_order(payload)
    if not sales_order:
        frappe.throw(_("sales_order or order_id is required."))

    cancelled = []
    if payload.get("order_id"):
        for invoice_name in frappe.get_all(
            "Sales Invoice",
            filters={CUSTOM_ORDER_ID_FIELD: payload.get("order_id"), "docstatus": 1},
            pluck="name",
        ):
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            invoice.cancel()
            cancelled.append({"doctype": "Sales Invoice", "name": invoice_name})

    order = frappe.get_doc("Sales Order", sales_order)
    if order.docstatus == 1:
        order.cancel()
        cancelled.append({"doctype": "Sales Order", "name": sales_order})
    elif order.docstatus == 0:
        order.add_comment("Info", payload.get("reason") or "Cancelled from Vortexus ecommerce channel.")

    return {"sales_order": sales_order, "cancelled": cancelled}


@frappe.whitelist()
def create_credit_note(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    sales_invoice = payload.get("sales_invoice") or _find_sales_invoice(payload)
    if not sales_invoice:
        frappe.throw(_("sales_invoice or order_id is required."))

    refund_reference = payload.get("refund_reference") or payload.get("payment_reference")
    if refund_reference:
        existing = frappe.db.get_value(
            "Sales Invoice",
            {
                "is_return": 1,
                CUSTOM_PAYMENT_REFERENCE_FIELD: refund_reference,
                "docstatus": ["!=", 2],
            },
            "name",
        )
        if existing:
            return {"credit_note": existing, "created": False}

    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

    credit_note = make_sales_return(sales_invoice)
    credit_note.set(CUSTOM_SOURCE_FIELD, SOURCE_VALUE)
    credit_note.set(CUSTOM_CHANNEL_FIELD, SALES_CHANNEL_VALUE)
    credit_note.set(CUSTOM_ORDER_NUMBER_FIELD, payload.get("order_number"))
    credit_note.set(CUSTOM_PAYMENT_PROVIDER_FIELD, payload.get("payment_provider"))
    credit_note.set(CUSTOM_PAYMENT_REFERENCE_FIELD, refund_reference)
    credit_note.remarks = payload.get("reason") or f"Vortexus ecommerce refund for {payload.get('order_number') or sales_invoice}"

    refund_amount = flt(payload.get("refund_amount") or 0)
    if refund_amount > 0:
        _scale_credit_note_to_amount(credit_note, refund_amount)

    credit_note.flags.ignore_permissions = True
    credit_note.insert(ignore_mandatory=True)
    if payload.get("submit", True):
        credit_note.submit()
    return {"credit_note": credit_note.name, "created": True}


def _sales_order_items(payload: dict) -> list[dict]:
    delivery_date = getdate(payload.get("delivery_date")) or nowdate()
    warehouse = payload.get("warehouse")
    items = []
    for row in payload.get("items") or []:
        item_code = row.get("item_code")
        if not item_code:
            frappe.throw(_("Every ecommerce order item must include item_code."))
        item = {
            "item_code": item_code,
            "qty": flt(row.get("qty") or 1),
            "rate": flt(row.get("rate") or 0),
            "delivery_date": getdate(row.get("delivery_date")) or delivery_date,
        }
        if warehouse or row.get("warehouse"):
            item["warehouse"] = row.get("warehouse") or warehouse
        if row.get("description"):
            item["description"] = row.get("description")
        items.append(item)
    return items


def _tag_ecommerce_doc(doc, payload: dict) -> None:
    doc.set(CUSTOM_SOURCE_FIELD, SOURCE_VALUE)
    doc.set(CUSTOM_CHANNEL_FIELD, SALES_CHANNEL_VALUE)
    doc.set(CUSTOM_ORDER_ID_FIELD, payload.get("order_id"))
    doc.set(CUSTOM_ORDER_NUMBER_FIELD, payload.get("order_number"))
    doc.set(CUSTOM_PAYMENT_PROVIDER_FIELD, payload.get("payment_provider"))
    doc.set(CUSTOM_PAYMENT_REFERENCE_FIELD, payload.get("payment_reference"))


def _find_sales_order(payload: dict) -> str | None:
    order_id = payload.get("order_id")
    if not order_id:
        return None
    return frappe.db.get_value("Sales Order", {CUSTOM_ORDER_ID_FIELD: order_id}, "name")


def _find_sales_invoice(payload: dict) -> str | None:
    if payload.get("sales_invoice"):
        return payload.get("sales_invoice")
    order_id = payload.get("order_id")
    if not order_id:
        return None
    return frappe.db.get_value("Sales Invoice", {CUSTOM_ORDER_ID_FIELD: order_id, "is_return": ["!=", 1]}, "name")


def _scale_credit_note_to_amount(credit_note, refund_amount: float) -> None:
    current_total = abs(flt(credit_note.grand_total))
    if current_total <= 0 or refund_amount >= current_total:
        return
    ratio = refund_amount / current_total
    for item in credit_note.items:
        item.qty = flt(item.qty) * ratio
