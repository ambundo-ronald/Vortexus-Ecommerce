from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from .constants import (
    CUSTOM_CHANNEL_FIELD,
    CUSTOM_ORDER_ID_FIELD,
    CUSTOM_ORDER_NUMBER_FIELD,
    CUSTOM_PAYMENT_PROVIDER_FIELD,
    CUSTOM_PAYMENT_REFERENCE_FIELD,
    CUSTOM_SOURCE_FIELD,
    CUSTOM_USER_ID_FIELD,
)


def after_install() -> None:
    create_vortexus_custom_fields()


def create_vortexus_custom_fields() -> None:
    custom_fields = {
        "Customer": [
            {
                "fieldname": CUSTOM_SOURCE_FIELD,
                "label": "Vortexus Source",
                "fieldtype": "Data",
                "insert_after": "customer_group",
                "read_only": 1,
            },
            {
                "fieldname": CUSTOM_USER_ID_FIELD,
                "label": "Vortexus User ID",
                "fieldtype": "Data",
                "insert_after": CUSTOM_SOURCE_FIELD,
                "unique": 1,
                "read_only": 1,
            },
        ],
        "Sales Order": ecommerce_order_fields("po_no"),
        "Sales Invoice": ecommerce_order_fields("po_no"),
        "Payment Entry": ecommerce_payment_fields("reference_no"),
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()


def ecommerce_order_fields(insert_after: str) -> list[dict]:
    return [
        {
            "fieldname": CUSTOM_SOURCE_FIELD,
            "label": "Vortexus Source",
            "fieldtype": "Data",
            "insert_after": insert_after,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_CHANNEL_FIELD,
            "label": "Vortexus Sales Channel",
            "fieldtype": "Data",
            "insert_after": CUSTOM_SOURCE_FIELD,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_ORDER_ID_FIELD,
            "label": "Vortexus Order ID",
            "fieldtype": "Data",
            "insert_after": CUSTOM_CHANNEL_FIELD,
            "unique": 1,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_ORDER_NUMBER_FIELD,
            "label": "Vortexus Order Number",
            "fieldtype": "Data",
            "insert_after": CUSTOM_ORDER_ID_FIELD,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_PAYMENT_PROVIDER_FIELD,
            "label": "Vortexus Payment Provider",
            "fieldtype": "Data",
            "insert_after": CUSTOM_ORDER_NUMBER_FIELD,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_PAYMENT_REFERENCE_FIELD,
            "label": "Vortexus Payment Reference",
            "fieldtype": "Data",
            "insert_after": CUSTOM_PAYMENT_PROVIDER_FIELD,
            "read_only": 1,
        },
    ]


def ecommerce_payment_fields(insert_after: str) -> list[dict]:
    return [
        {
            "fieldname": CUSTOM_SOURCE_FIELD,
            "label": "Vortexus Source",
            "fieldtype": "Data",
            "insert_after": insert_after,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_ORDER_NUMBER_FIELD,
            "label": "Vortexus Order Number",
            "fieldtype": "Data",
            "insert_after": CUSTOM_SOURCE_FIELD,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_PAYMENT_PROVIDER_FIELD,
            "label": "Vortexus Payment Provider",
            "fieldtype": "Data",
            "insert_after": CUSTOM_ORDER_NUMBER_FIELD,
            "read_only": 1,
        },
        {
            "fieldname": CUSTOM_PAYMENT_REFERENCE_FIELD,
            "label": "Vortexus Payment Reference",
            "fieldtype": "Data",
            "insert_after": CUSTOM_PAYMENT_PROVIDER_FIELD,
            "read_only": 1,
        },
    ]

