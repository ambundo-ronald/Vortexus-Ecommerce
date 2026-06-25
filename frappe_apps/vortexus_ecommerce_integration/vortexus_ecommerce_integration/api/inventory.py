from __future__ import annotations

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_item_stock(item_code: str, warehouse: str | None = None) -> dict:
    if not item_code:
        frappe.throw("item_code is required.")

    filters = {"item_code": item_code}
    if warehouse:
        filters["warehouse"] = warehouse

    rows = frappe.get_all(
        "Bin",
        filters=filters,
        fields=["item_code", "warehouse", "actual_qty", "reserved_qty", "projected_qty"],
    )
    available_qty = sum(flt(row.actual_qty) - flt(row.reserved_qty) for row in rows)
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "available_qty": available_qty,
        "warehouses": rows,
    }


@frappe.whitelist()
def get_many_item_stock(item_codes: list[str] | str, warehouse: str | None = None) -> list[dict]:
    item_codes = frappe.parse_json(item_codes or [])
    if not isinstance(item_codes, list):
        frappe.throw("item_codes must be a list.")
    return [get_item_stock(item_code, warehouse) for item_code in item_codes]
