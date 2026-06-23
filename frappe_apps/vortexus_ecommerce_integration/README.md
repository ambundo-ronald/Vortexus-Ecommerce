# Vortexus Ecommerce Integration

Frappe/ERPNext bridge app for the Vortexus storefront.

This app is intentionally separate from the Django backend. It gives ERPNext a
small Vortexus-specific layer for ecommerce source tracking, customer sync,
sales order/invoice tagging, payment references, and inventory reads.

## Scope

- Mark ERPNext Customers, Sales Orders, Sales Invoices, and Payment Entries as
  coming from `Ecommerce`.
- Store Vortexus external IDs on ERPNext documents for idempotent sync.
- Create/update ecommerce customers, contacts, and addresses.
- Create ecommerce Sales Orders.
- Create Sales Invoices and Payment Entries for paid orders.
- Cancel ecommerce Sales Orders and related Sales Invoices when the storefront
  order is cancelled.
- Expose whitelisted inventory helpers for the backend to query ERPNext stock.

## Install

From an ERPNext bench:

```bash
bench get-app /path/to/vortexus/frappe_apps/vortexus_ecommerce_integration
bench --site your-site install-app vortexus_ecommerce_integration
bench --site your-site migrate
```

## Backend Integration

The Django backend should call these whitelisted methods through ERPNext's REST
API:

- `vortexus_ecommerce_integration.api.customer.upsert_customer`
- `vortexus_ecommerce_integration.api.order.create_sales_order`
- `vortexus_ecommerce_integration.api.order.create_sales_invoice`
- `vortexus_ecommerce_integration.api.order.cancel_sales_order`
- `vortexus_ecommerce_integration.api.order.create_credit_note`
- `vortexus_ecommerce_integration.api.inventory.get_item_stock`

All writes should include a stable Vortexus ID so retries are idempotent.

## Customer Payload

```json
{
  "user_id": "123",
  "email": "buyer@example.com",
  "first_name": "Jane",
  "last_name": "Buyer",
  "phone": "+254700000000",
  "customer_group": "Ecommerce",
  "territory": "Kenya",
  "billing_address": {
    "address_line1": "Industrial Area",
    "city": "Nairobi",
    "country": "Kenya"
  }
}
```

## Sales Order Payload

```json
{
  "order_id": "99",
  "order_number": "VX-1001",
  "customer": "Jane Buyer",
  "company": "Vortexus Industrial",
  "currency": "KES",
  "payment_provider": "Pesapal",
  "payment_reference": "PESA-123",
  "items": [
    {
      "item_code": "ERP-ITEM-25",
      "qty": 2,
      "rate": 1500,
      "warehouse": "Stores - VI"
    }
  ]
}
```

## Sales Invoice And Payment Payload

```json
{
  "order_id": "99",
  "order_number": "VX-1001",
  "sales_order": "SO-ECOM-2026-00001",
  "payment_provider": "Pesapal",
  "payment_reference": "PESA-123",
  "create_payment_entry": true,
  "bank_account": "Pesapal Clearing - VI"
}
```

## Credit Note Payload

```json
{
  "order_id": "99",
  "order_number": "VX-1001",
  "sales_invoice": "SI-ECOM-2026-00001",
  "payment_provider": "Pesapal",
  "payment_reference": "PESA-123",
  "refund_reference": "REFUND-PAY-123",
  "refund_amount": "100.00",
  "reason": "Returned item"
}
```

## Inventory Payload

```json
{
  "item_codes": ["ERP-ITEM-25", "ERP-ITEM-26"],
  "warehouse": "Stores - VI"
}
```

## Production Notes

- Create an `Ecommerce` Customer Group in ERPNext before launch.
- Create or select a default ecommerce warehouse.
- Create a Pesapal clearing bank/cash account for Payment Entries.
- Keep ERPNext as the accounting and inventory source of truth.
- Let the Django backend own storefront UX, checkout session state, and Pesapal
  callbacks, then sync final business documents into ERPNext.
- This app creates ERPNext credit notes for refund accounting. Actual payment
  gateway refunds still need to be executed/reconciled according to the gateway
  provider's process.
