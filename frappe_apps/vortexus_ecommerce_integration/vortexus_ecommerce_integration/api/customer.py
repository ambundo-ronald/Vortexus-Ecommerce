from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr, validate_phone_number

from vortexus_ecommerce_integration.constants import (
    CUSTOM_SOURCE_FIELD,
    CUSTOM_USER_ID_FIELD,
    SOURCE_VALUE,
)


@frappe.whitelist()
def upsert_customer(payload: dict | None = None) -> dict:
    payload = frappe.parse_json(payload or {})
    user_id = cstr(payload.get("user_id")).strip()
    email = cstr(payload.get("email")).strip()
    if not user_id and not email:
        frappe.throw(_("Either user_id or email is required to sync a Vortexus customer."))

    customer_name = _customer_name(payload)
    customer = _find_customer(user_id, email)
    if customer:
        doc = frappe.get_doc("Customer", customer)
        doc.customer_name = customer_name
        doc.customer_group = payload.get("customer_group") or doc.customer_group or "Ecommerce"
        doc.territory = payload.get("territory") or doc.territory or "All Territories"
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": payload.get("customer_type") or "Individual",
                "customer_group": payload.get("customer_group") or "Ecommerce",
                "territory": payload.get("territory") or "All Territories",
            }
        )

    doc.set(CUSTOM_SOURCE_FIELD, SOURCE_VALUE)
    if user_id:
        doc.set(CUSTOM_USER_ID_FIELD, user_id)
    doc.flags.ignore_permissions = True
    doc.save()

    if email or payload.get("phone"):
        _upsert_contact(doc.name, payload)
    if payload.get("billing_address"):
        _upsert_address(doc.name, payload["billing_address"], "Billing", email)
    if payload.get("shipping_address"):
        _upsert_address(doc.name, payload["shipping_address"], "Shipping", email)

    return {"customer": doc.name, "created": not bool(customer)}


def _find_customer(user_id: str, email: str) -> str | None:
    if user_id:
        customer = frappe.db.get_value("Customer", {CUSTOM_USER_ID_FIELD: user_id}, "name")
        if customer:
            return customer
    if email:
        contact = frappe.db.sql(
            """
            select parent
            from `tabDynamic Link`
            where parenttype = 'Contact'
              and link_doctype = 'Customer'
              and parent in (
                select parent from `tabContact Email` where email_id = %s
              )
            limit 1
            """,
            email,
            as_dict=True,
        )
        if contact:
            return frappe.db.get_value("Dynamic Link", {"parent": contact[0].parent, "link_doctype": "Customer"}, "link_name")
    return None


def _customer_name(payload: dict) -> str:
    company_name = cstr(payload.get("company_name")).strip()
    if company_name:
        return company_name
    full_name = " ".join(part for part in [cstr(payload.get("first_name")).strip(), cstr(payload.get("last_name")).strip()] if part)
    return full_name or cstr(payload.get("email")).strip() or "Vortexus Online Customer"


def _upsert_contact(customer: str, payload: dict) -> None:
    email = cstr(payload.get("email")).strip()
    phone = cstr(payload.get("phone")).strip()
    contact_name = frappe.db.get_value("Contact Email", {"email_id": email}, "parent") if email else None
    contact = frappe.get_doc("Contact", contact_name) if contact_name else frappe.new_doc("Contact")
    contact.first_name = cstr(payload.get("first_name")).strip() or _customer_name(payload)
    contact.last_name = cstr(payload.get("last_name")).strip()
    if email and not any(row.email_id == email for row in contact.email_ids):
        contact.append("email_ids", {"email_id": email, "is_primary": 1})
    if phone and validate_phone_number(phone, throw=False) and not any(row.phone == phone for row in contact.phone_nos):
        contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})
    if not any(link.link_doctype == "Customer" and link.link_name == customer for link in contact.links):
        contact.append("links", {"link_doctype": "Customer", "link_name": customer})
    contact.flags.ignore_permissions = True
    contact.save()


def _upsert_address(customer: str, address: dict, address_type: str, email: str | None = None) -> None:
    title = cstr(address.get("address_title")).strip() or customer
    linked_addresses = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
        pluck="parent",
    )
    existing = frappe.db.get_value("Address", {"name": ["in", linked_addresses], "address_type": address_type}, "name") if linked_addresses else None
    doc = frappe.get_doc("Address", existing) if existing else frappe.new_doc("Address")
    doc.address_title = title
    doc.address_type = address_type
    doc.address_line1 = address.get("address_line1") or address.get("line1") or "Address Line 1"
    doc.address_line2 = address.get("address_line2") or address.get("line2")
    doc.city = address.get("city")
    doc.state = address.get("state")
    doc.pincode = address.get("pincode") or address.get("postal_code")
    doc.country = address.get("country") or "Kenya"
    doc.email_id = email
    phone = cstr(address.get("phone")).strip()
    if phone and validate_phone_number(phone, throw=False):
        doc.phone = phone
    if not any(link.link_doctype == "Customer" and link.link_name == customer for link in doc.links):
        doc.append("links", {"link_doctype": "Customer", "link_name": customer})
    doc.flags.ignore_permissions = True
    doc.save()
