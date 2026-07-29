# Finance and Reconciliation Task List

This is the implementation checklist for making Reesolmart financially safe for production. The goal is to track every customer payment, supplier payable, refund, cancellation, payout, and ERPNext finance sync without exposing Reesolmart margin or selling-price data to suppliers.

## Phase 1: Audit Current Finance Flow

- [x] Audit existing checkout, payment, order, supplier allocation, and ERPNext sync code.
- [x] Confirm when an order is created relative to payment confirmation.
- [x] Confirm which payment providers create `PaymentSession` records.
- [x] Confirm whether provider callbacks and manual verification update the same payment record.
- [x] Confirm when supplier allocations are created from order lines.
- [x] Confirm stock deduction, stock release, and cancelled order behavior.
- [x] Document all current payment/order statuses and their meaning.

Acceptance criteria:
- [x] We know exactly where money enters the system.
- [x] We know where supplier payable amounts are calculated.
- [x] We know every current gap before adding new finance tables.

### Phase 1 Audit   

Current checkout and payment flow:
- Basket item add/update creates or adjusts stock reservations through `sync_basket_line_reservation`.
- Payment initialization creates a `PaymentSession` before order placement.
- Order placement requires a `payment_reference`.
- For prepayment methods, order placement is blocked unless the `PaymentSession` status is `authorized` or `paid`.
- Order placement validates payment amount, currency, basket, shipping method, and country against the current checkout totals.
- After the order is created, `link_payment_to_order` links the `PaymentSession` to the Oscar order and creates Oscar payment `Source` and `Transaction` rows.
- `ensure_supplier_order_groups` then creates supplier order groups and supplier line allocations from the order lines.
- `basket.submit()` happens after payment linking and supplier grouping.
- Order export to ERPNext is queued after order placement.

Current payment records:
- `PaymentSession` is the main payment object.
- `PaymentEvent` is an audit trail for provider submission, callbacks, status queries, status changes, gateway errors, and order linking.
- The existing `payment_reconciliation(payment_session)` function is computed on demand. It is useful for display, but it is not a durable reconciliation ledger.
- Current provider-backed methods that create payment sessions are:
  - M-Pesa
  - Pesapal
  - Airtel Money
  - Card
  - generic configured payment initialization  
- Offline methods can be initialized as `authorized` depending on payment method configuration.

Current payment statuses:
- `initialized`: session created but not necessarily submitted to a provider.
- `pending`: waiting for provider/customer confirmation.
- `authorized`: accepted/authorized but not necessarily cash-settled.
- `paid`: confirmed paid.
- `failed`: provider/customer payment failed.
- `cancelled`: payment cancelled.

Current order and fulfillment statuses:
- Oscar order status starts from `OSCAR_INITIAL_ORDER_STATUS`, usually `Pending`.
- Admin order status updates map to supplier line/group statuses:
  - `Pending` -> `pending`
  - `Processing` -> `processing`
  - `Packed` -> `packed`
  - `Shipped` -> `shipped`
  - `Delivered` -> `delivered`
  - `Cancelled` -> `cancelled`
- Supplier line status updates can also move line/group/order fulfillment status.

Current stock behavior:
- Adding to basket creates a reservation record but does not consume stock permanently.
- Removing a basket line releases the reservation.
- Before order placement, `prepare_basket_for_order_submission` verifies availability and deletes basket reservation records.
- Stock is consumed when fulfillment changes a line to `shipped` or `delivered`.
- Stock allocation is cancelled when a line is cancelled before shipment/delivery.

Current supplier finance behavior:
- `SupplierOrderGroup` stores supplier-facing group totals based on customer order line values and allocated shipping. This is operational grouping, not payout accounting.
- `SupplierOrderLineAllocation` stores:
  - customer unit price
  - supplier unit cost
  - supplier total cost
  - gross margin
  - payout status
- Supplier payable is currently calculated from `SupplierOrderLineAllocation.supplier_total_cost`.
- Supplier dashboard has been tightened to show supplier payable amounts only.
- Admin/account manager visibility can still include gross margin and customer selling values.

Current ERPNext behavior:
- Customer sync exists and marks mapping metadata source as `ecommerce`.
- Sales Order export exists after order placement.
- Paid order accounting export exists after a successful payment is linked to an order.
- Cancellation sync exists for cancelled orders.
- Refund credit note export exists from the admin refund action.
- ERPNext sync is asynchronous and does not block checkout.

Phase 1 gaps before new finance tables:
- There is no durable `PaymentReconciliation` table.
- There is no immutable finance ledger for provider settlements, gateway fees, duplicate references, amount mismatches, or manual reconciliation decisions.
- Supplier allocations double as payable records, but they are not enough for a proper payable ledger because reversals, holds, disputes, payout batches, and debit adjustments are not modelled separately.
- Refund requests are stored in `PaymentSession.metadata`, not a structured refund ledger.
- Provider fees and bank settlement amounts are not recorded.
- `authorized` and `paid` need clear finance meaning per method before payout automation.
- Cancellations and returns need explicit payable reversal rules.
- ERPNext accounting sync should be driven from durable finance ledger events, not only raw payment/order events.

Phase 2 decision:
- Do not change Pesapal or provider-specific logic in this phase.
- Add finance models around existing payment/order data first.
- Keep checkout fast and keep ERPNext sync asynchronous.
- Treat `PaymentSession` as the operational payment record and the new reconciliation table as the finance control record.

## Phase 2: Payment Reconciliation Ledger

- [x] Add a `PaymentReconciliation` model linked to `PaymentSession` and order.
- [x] Track provider, provider reference, merchant reference, currency, expected amount, paid amount, fees, settled amount, and reconciliation status.
- [x] Add statuses:
  - pending
  - matched
  - amount_mismatch
  - duplicate
  - failed
  - cancelled
  - reversed
  - refunded
  - manual_review
- [x] Store raw provider/payment payload safely for audit.
- [x] Record who manually reviewed or corrected a reconciliation entry.
- [x] Add admin workflow for manual review/correction.
- [x] Add immutable audit events for every manual reconciliation status change.
- [x] Flag duplicate provider references for finance review.
- [x] Enforce duplicate provider references before fulfillment/payout.

Acceptance criteria:
- [x] Every new payment attempt creates or refreshes a reconciliation row.
- [x] Paid orders can have a matched reconciliation record.
- [x] Mismatches are visible to admin payment logs and Django admin.
- [x] Mismatches block fulfillment or payout.

Phase 2 implementation notes:
- Reconciliation rows are created/refreshed from provider-neutral payment service hooks:
  - payment initialization
  - payment confirmation
  - payment/order linking
- Existing payment sessions can be backfilled with:
  - `python manage.py migrate payments`
  - `python manage.py sync_payment_reconciliations`
- No Pesapal-specific code was changed in this phase.
- Docker was not running during local verification, so container migration/rebuild still needs to be run before review.
- Admin finance can now manually review a reconciliation row through `/api/v1/admin/finance/reconciliation/<id>/`.
- Manual reconciliation changes stamp reviewer details, append a finance note, create a payment event, and write an audit log event.
- Orders cannot move to processing, packing, shipping, or delivery while reconciliation is pending, duplicate, mismatched, failed, cancelled, refunded, reversed, or under manual review.
- Supplier payout batches cannot be created unless every included payable belongs to an order with matched reconciliation.

## Phase 3: Supplier Payable Ledger

- [x] Add a supplier payable ledger model linked to:
  - supplier profile
  - supplier partner
  - order
  - order line
  - supplier offer
  - stock record
- [x] Store supplier unit cost, quantity sold, supplier payable total, currency, and payout status.
- [x] Add payout statuses:
  - pending
  - payable
  - on_hold
  - approved
  - paid
  - disputed
  - reversed
- [x] Ensure supplier payable is calculated from supplier cost, not storefront selling price.
- [x] Ensure supplier dashboard only reads supplier payable fields.
- [ ] Keep customer selling price, shipping margin, gateway fees, and gross margin admin-only.
- [x] Prevent supplier payable creation for failed or unpaid orders.

Acceptance criteria:
- Admin can see what is owed to each supplier.
- Supplier can see only their own payable amount.
- Reesolmart margin is never returned by supplier-facing APIs.

Phase 3 implementation notes:
- `SupplierPayableLedger` is linked one-to-one to `SupplierOrderLineAllocation`.
- Supplier payable totals are copied from supplier cost fields, not customer selling price.
- Ledger rows refresh when supplier allocations are created, admin order status changes, and supplier line fulfillment status changes.
- Existing allocations can be backfilled with:
  - `python manage.py migrate marketplace`
  - `python manage.py sync_supplier_payables`
- Current implementation creates pending control rows for unpaid orders, but only moves them to `payable` after a confirmed payment exists.
- Failed or cancelled/unpaid orders now keep supplier payable rows reversed or pending; they cannot become payable or enter payout batches.
- Confirmed payments with duplicate/mismatched/manual-review reconciliation put supplier payable rows on hold until finance clears them.

## Phase 4: Admin Finance Dashboard

- [x] Add dashboard page `/finance` or `/finance/reconciliation`.
- [x] Add KPI cards:
  - confirmed customer collections
  - unreconciled payments
  - supplier payables
  - supplier paid out
  - refunds
  - gateway fees
  - gross margin
  - net margin
- [x] Add reconciliation table with filters by date, provider, status, currency, order number, and reference.
- [x] Add supplier payable table with filters by supplier, payout status, order, date, and account manager.
- [x] Add order finance detail panel showing:
  - customer amount paid
  - payment provider/reference
  - supplier payable per line
  - margin per line
  - shipping charged
  - shipping cost if available
  - refund/reversal status
- [x] Restrict page to platform admin and finance-authorized staff only.

Acceptance criteria:
- Admin can identify paid, unpaid, mismatched, payable, and paid-out amounts from one finance area.
- Account managers can see only suppliers assigned to them unless they have full finance permission.

Phase 4 implementation notes:
- Added platform-admin backend summary endpoint at `/api/v1/admin/finance/summary/`.
- Added dashboard page `/finance` with KPI cards and summary tables for payment status, payment method, reconciliation status, and supplier payable status.
- Added platform-admin backend record endpoints:
  - `/api/v1/admin/finance/reconciliation/`
  - `/api/v1/admin/finance/supplier-payables/`
- Added dashboard reconciliation and supplier payable tables with search, status, date, currency, order, provider/reference, supplier, and account manager filters.
- Added platform-admin order finance drill-down endpoint at `/api/v1/admin/finance/orders/<order_number>/`.
- Added dashboard order finance lookup panel showing payment, reconciliation, shipping, supplier payable, refunds, gross margin, and line-level margin/payable details.
- Added reusable finance access logic. Superusers have finance access automatically; staff can be granted access through Django groups `finance`, `finance_viewer`, `finance_operator`, `finance_approver`, or payment view permissions.
- Dashboard session now exposes `permissions.can_access_finance`; account managers only see/reach `/finance` when finance-authorized.

## Phase 5: Supplier Payout Workflow

- [x] Add payout batch model.
- [x] Allow admin to select payable supplier ledger entries and create a payout batch.
- [x] Add payout batch statuses:
  - draft
  - pending_approval
  - approved
  - paid
  - cancelled
- [x] Store payout method, payout reference, paid date, notes, and approved by.
- [x] Support exporting payout batch to CSV.
- [x] Support uploading bank/M-Pesa payout evidence.
- [x] Mark included payable ledger entries as paid after payout confirmation.
- [x] Notify supplier when payout is marked paid.

Acceptance criteria:
- [x] Supplier payments are batch-controlled, auditable, and reversible.
- [x] Admin can prove why and when a supplier was paid.

Phase 5 implementation notes:
- Added supplier payout batch and payout batch entry models.
- Added backend finance payout APIs for listing, creating, submitting, approving, marking paid, cancelling, and CSV export.
- Added dashboard payout batch controls on `/finance`.
- Current evidence support stores an evidence URL; actual file upload/storage is still pending.
- Payout batches now support stored evidence file upload plus optional evidence URL.
- Supplier payout-paid email is queued when a payout batch is marked paid.

## Phase 6: Refunds, Cancellations, and Returns

- [x] Define cancellation rules before payment, after payment, after fulfillment, and after supplier payout.
- [x] Add refund ledger model linked to payment reconciliation, order, and order lines.
- [x] Support full and partial refunds.
- [x] On failed payment:
  - mark payment failed
  - do not create payable supplier ledger
  - do not fulfill order
- [x] On cancelled unpaid order:
  - release reserved stock
  - cancel payment session
  - create no supplier payable
- [x] On cancelled paid order before fulfillment:
  - create refund entry
  - release stock
  - reverse supplier payable
- [x] On return after fulfillment:
  - create refund/return entry
  - restock only if item is accepted back
  - reverse or adjust supplier payable
- [x] If supplier was already paid, create supplier debit or negative adjustment.

Acceptance criteria:
- [x] No supplier is paid for failed/cancelled unpaid orders.
- [x] Refunds and returns are visible in finance reports.
- [x] Supplier payable balances remain correct after reversals.

Phase 6 implementation notes:
- Added `PaymentRefundLedger` for refund, cancellation, return, and adjustment records.
- Admin refund requests now create a durable refund ledger row while retaining older `PaymentSession.metadata.refund_requests` compatibility.
- Finance summary and order finance drill-down now read refund totals from the ledger first, with metadata fallback for older records.
- Added `/api/v1/admin/finance/refunds/` with filters for status, type, currency, order, reference, and date range.
- Added refund/reversal ledger table to the dashboard `/finance` page.
- Existing order cancellation already refreshes supplier payable rows and reverses unpaid/cancelled allocations.
- Added `SupplierPayableAdjustment` so refunds against already-paid supplier rows create pending-review supplier debit adjustments.
- Added formal full vs partial refund scope and completion states:
  - partial/full requested
  - partial/full submitted
  - partial/full completed
  - failed
  - cancelled
- Added return intake/restock workflow:
  - admin can create a return case against a paid payment and order line
  - return cases move through requested, approved, received, accepted, rejected, refunded, or cancelled
  - accepted returns can restock, quarantine, scrap, or reject inventory
  - restocked returns add accepted quantity back to the order line stock record
  - accepted returns create a structured return refund ledger and supplier payable reversal/debit adjustment
  - supplier payable is protected from double adjustment if a return is accepted then later marked refunded
- Failed linked payments now mark the order as failed when it has not fulfilled yet, cancel unfulfilled allocations, and refresh supplier payable rows.
- Cancelling an unpaid order cancels non-success payment sessions, releases unfulfilled stock allocations, and keeps supplier payable rows non-payable.
- Cancelling a paid order before fulfillment creates a cancellation refund ledger, releases unfulfilled stock allocations, reverses unpaid supplier payables, and queues ERPNext credit-note export.
- Orders with shipped or delivered lines cannot be cancelled through the normal cancellation path; they must go through return intake.

## Phase 7: ERPNext Finance Sync

- [x] Decide ERPNext source-of-truth boundaries:
  - ecommerce owns checkout speed and payment verification
  - ERPNext owns formal accounting, tax, and finance reporting
- [x] Sync customers with source field `ecommerce`.
- [x] Sync Sales Order with source field `ecommerce`.
- [x] Sync Sales Invoice with ecommerce order reference.
- [x] Sync Payment Entry after payment reconciliation is matched.
- [x] Sync cancellation/return/refund as cancellation, credit note, or journal entry depending on ERPNext rules.
- [x] Sync supplier payout batches as supplier payment records or custom ERPNext document.
- [x] Add ERPNext sync status to reconciliation, payable, refund, and payout records.
- [x] Add retry queue for failed ERPNext sync events.

Acceptance criteria:
- ERPNext receives clean finance events after ecommerce has verified them.
- Checkout does not wait on ERPNext.
- Failed ERPNext sync can be retried without duplicating accounting records.

Phase 7 implementation notes:
- Customer sync, Sales Order export, Sales Invoice export, Payment Entry export, order cancellation sync, refund credit note export, and supplier payout batch export all run asynchronously.
- Reconciliation, refund, payable, payout batch, and supplier adjustment records now carry ERPNext sync status/reference/message/timestamp fields.
- Supplier payout batches export only after the batch is marked `paid`; included payable ledger entries inherit the ERPNext payout reference.
- ERPNext export failures are retried through Celery and recorded on the finance ledger rows for admin review.
- Return-after-fulfillment ERPNext rule is now explicit: accepted/refunded ecommerce returns export as ERPNext credit notes against the ecommerce Sales Invoice, including return line, accepted quantity, restock decision, and return reference metadata.

## Phase 8: Finance Permissions and Security

- [ ] Add finance-specific permissions or roles:
  - finance viewer
  - finance operator
  - finance approver
  - platform admin
- [ ] Prevent suppliers from accessing selling price, customer payment total, gateway fee, margin, and payout batches for other suppliers.
- [ ] Mask sensitive customer/payment data in finance tables where not needed.
- [ ] Add audit logging for finance reads and all finance mutations.
- [ ] Add two-person approval for payout batches above a configurable threshold.
- [ ] Add export audit trail for finance CSV downloads.

Acceptance criteria:
- Supplier users only see their own payable view.
- Finance operations are auditable and permission-controlled.
- Payout approval cannot be silently manipulated.

## Phase 9: Reports and Exports

- [ ] Add daily sales reconciliation report.
- [ ] Add provider settlement report.
- [ ] Add supplier payable aging report.
- [ ] Add supplier payout report.
- [ ] Add refund and reversal report.
- [ ] Add margin report by product, category, supplier, and order.
- [ ] Add CSV export for all finance reports.
- [ ] Add date range and currency filters.

Acceptance criteria:
- Admin can close daily finance without touching the database.
- Finance data can be exported for accountant review.

## Phase 10: Tests and Go-Live Readiness

- [ ] Add backend tests for payment reconciliation creation.
- [ ] Add backend tests for duplicate payment references.
- [ ] Add backend tests for supplier payable creation.
- [ ] Add backend tests for supplier payable reversal.
- [ ] Add backend tests for payout batch workflow.
- [ ] Add backend tests for supplier finance data isolation.
- [ ] Add frontend tests or manual QA checklist for finance dashboard.
- [ ] Test Pesapal success, failure, timeout, duplicate callback, and manual verification flows.
- [ ] Test cancellation and return scenarios.
- [ ] Test ERPNext sync retry and idempotency.

Acceptance criteria:
- Finance logic handles success, failure, duplicate, cancellation, refund, and payout cases.
- Supplier users cannot see Reesolmart figures.
- Admin can reconcile orders before real customer launch.

## Recommended First Implementation Slice

- [x] Create `PaymentReconciliation` model and migration.
- [x] Create supplier payable ledger model and migration.
- [x] Generate reconciliation record when payment is initiated and update it when verified.
- [x] Generate supplier payable rows only after payment is confirmed and order exists.
- [x] Add admin finance summary endpoint.
- [x] Add dashboard finance page with reconciliation and supplier payable tables.
- [ ] Keep supplier dashboard backed only by supplier payable totals.
