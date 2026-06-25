# Launch Payment And ERP Checklist

Use this checklist for the final external validation before accepting live customer payments.

## ERPNext App Install

- Install `frappe_apps/vortexus_ecommerce_integration` into the ERPNext site.
- Run `bench --site <site> migrate`.
- Confirm custom fields appear on Customer, Sales Order, Sales Invoice, and Payment Entry.
- Create/confirm:
  - `Ecommerce` Customer Group
  - Kenya territory or the correct launch territory
  - default warehouse
  - Pesapal clearing bank/cash account
  - tax/accounts configuration for ecommerce orders

## Dashboard Integration Settings

In Dashboard `/integrations`, enable:

- `Use Vortexus ERPNext app`
- `Sync customers`
- `Export sales orders`
- `Export invoices and payments`
- `Sync cancellations`
- `Sync refund credit notes`

Set:

- customer group: `Ecommerce`
- territory: `Kenya`
- Pesapal clearing account
- delivery days
- default company
- default warehouse

## End-To-End Test

1. Register a storefront customer.
2. Confirm ERPNext Customer is created with source `Ecommerce`.
3. Place a Pesapal sandbox order.
4. Confirm backend payment status becomes `paid`.
5. Confirm ERPNext Sales Order is created.
6. Confirm ERPNext Sales Invoice is created.
7. Confirm ERPNext Payment Entry is created with Pesapal reference.
8. Cancel an order from admin and confirm ERPNext cancellation sync.
9. Request refund from Dashboard `/payment-logs` and confirm:
   - Pesapal refund request is accepted for processing.
   - ERPNext Credit Note is created.
   - finance reconciles final settlement.

## Security

- Confirm `.env` files are not committed.
- Rotate any Cloudflare tunnel token that was pasted into chat or screenshots.
- Use environment-backed ERPNext credentials in production.
- Confirm production `ALLOWED_HOSTS`, CORS, and CSRF values.
- Confirm Pesapal sandbox credentials are replaced with production credentials only at launch cutover.
