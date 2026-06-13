# Supplier Onboarding to Selling Task List

This is the implementation checklist for turning Vortexus into a controlled multi-supplier marketplace. The goal is to let suppliers apply, get approved, upload products, pass product moderation, sell through the storefront, and fulfill only the orders assigned to them.

## Phase 1: Confirm Current Supplier Foundation

- [ ] Audit existing supplier models, serializers, views, and frontend routes.
- [ ] Confirm each supplier user is linked to exactly one `SupplierProfile`.
- [ ] Confirm each `SupplierProfile` is linked to one Oscar `Partner`.
- [ ] Confirm supplier product queries are scoped by `stockrecords__partner`.
- [ ] Confirm supplier order queries are scoped by supplier partner/order group.
- [ ] Document current supplier API endpoints and expected response payloads.

Acceptance criteria:
- We know exactly what already works.
- We know which supplier features are backend-only, frontend-only, or missing.
- No supplier endpoint exposes products, orders, customers, or financial data from another supplier.

## Phase 2: Supplier Application and Account Creation

- [ ] Define required supplier application fields:
  - company name
  - contact name
  - email
  - phone
  - country
  - website
  - registration number
  - tax/PIN/VAT number
  - business category
  - notes
- [ ] Add optional document upload fields for business registration, tax certificate, and authorization letter.
- [x] Ensure supplier application creates `SupplierProfile` with `status = pending`.
- [x] Prevent duplicate supplier profiles for the same user.
- [x] Add throttling/rate limiting for supplier applications.
- [x] Add audit event for supplier application submission.
- [ ] Add email notification to internal team when a supplier applies.
- [x] Add email confirmation to supplier after application submission.

Acceptance criteria:
- A logged-in customer can apply to become a supplier.
- The account remains pending until staff approval.
- Supplier cannot sell while pending.

## Phase 3: Admin Supplier Review Workflow

- [ ] Improve admin supplier list with filters for pending, approved, rejected, suspended.
- [ ] Add supplier detail page with application data, documents, partner, assigned account manager, and audit history.
- [ ] Add admin actions:
  - approve supplier
  - reject supplier
  - suspend supplier
  - request more information
  - reactivate supplier
- [x] Add reason/comment field for every status change.
- [x] Add assigned account manager field.
- [x] On approval, create or link Oscar `Partner`.
- [ ] On approval, ensure supplier user gets supplier portal access.
- [x] Send status-change email to supplier.
- [x] Audit log every admin action.

Acceptance criteria:
- Staff can review and approve suppliers from the dashboard.
- Supplier status changes are traceable.
- Approved suppliers are connected to a partner record before selling.

## Phase 4: Supplier Portal Access Control

- [ ] Keep supplier users out of `/admin`.
- [x] Add or confirm `/supplier` portal routes.
- [x] Ensure supplier portal uses supplier-only route guards.
- [x] Show pending suppliers a limited portal:
  - application status
  - profile details
  - requested changes
  - no product upload
  - no order access
- [x] Show approved suppliers full portal:
  - dashboard
  - products
  - product upload
  - product approval statuses
  - orders
  - fulfillment updates
- [x] Show suspended suppliers restricted portal:
  - account status
  - support/contact guidance
  - no writes
- [ ] Add backend permission tests for supplier access rules.

Acceptance criteria:
- Supplier users only see supplier screens.
- Supplier permissions are enforced by backend, not just hidden in frontend.

## Phase 5: Supplier Product Upload Workflow

- [ ] Define supplier product fields:
  - title
  - SKU
  - brand
  - category
  - description
  - images
  - price
  - currency
  - stock quantity
  - lead time
  - warranty/return notes
  - technical/spec attributes
- [x] Build supplier product create/edit form.
- [x] Support image uploads with validation.
- [x] Link uploaded product to supplier partner stock record.
- [x] Default new supplier products to `approval_status = pending_review`.
- [x] Prevent pending products from appearing on storefront.
- [x] Prevent pending products from entering search index.
- [ ] Allow supplier to save drafts before submission.
- [x] Add supplier-visible product statuses:
  - draft
  - pending review
  - changes requested
  - approved
  - rejected
  - suspended
- [x] Audit log product creation and updates.

Acceptance criteria:
- Approved suppliers can upload products.
- New products do not go live until reviewed.
- Supplier can see their uploaded products and current approval status.

## Phase 6: Product Moderation by Account Manager

- [x] Add backend admin product moderation queue API.
- [x] Add admin product moderation queue UI.
- [ ] Filter moderation queue by supplier, category, brand, status, account manager.
- [ ] Add product review detail screen with:
  - supplier details
  - product data
  - images
  - price
  - inventory
  - category/brand
  - change history
- [x] Add backend moderation actions:
  - approve
  - reject
  - request changes
  - suspend product
  - publish/unpublish
- [x] Require reason/comment for reject, request changes, and suspend.
- [ ] Notify supplier on moderation decision.
- [x] On approval, mark product public and searchable.
- [x] On rejection/suspension, hide from storefront and search.
- [x] Reindex search after approval/status changes.

Acceptance criteria:
- No supplier product goes live without approval.
- Staff have a clear queue for product review.
- Search and category pages only show approved/public products.

## Phase 7: Catalogue Organization for Marketplace Quality

- [ ] Require category for every supplier product.
- [ ] Require brand or manufacturer field where applicable.
- [ ] Validate category against approved category tree.
- [ ] Add category-specific required attributes where needed.
- [ ] Normalize brand names to avoid duplicates.
- [ ] Add duplicate product detection by SKU, title, brand, and supplier.
- [ ] Decide whether duplicate supplier offers should share one product detail page or create separate product pages.
- [ ] Ensure filters work by category, brand, supplier offer, price, stock, and search query.
- [ ] Ensure photo search only returns approved/public products.

Acceptance criteria:
- Supplier uploads improve catalogue quality instead of creating messy duplicates.
- Storefront category, brand, text search, and photo search stay reliable.

## Phase 8: Orders and Supplier Fulfillment

- [ ] Confirm checkout assigns each order line to the correct partner/supplier.
- [ ] Confirm multi-supplier orders create supplier order groups.
- [ ] Supplier sees only their own order groups and lines.
- [ ] Supplier can update line status:
  - pending
  - processing
  - packed
  - shipped
  - delivered
  - cancelled
- [ ] Add tracking reference and fulfillment notes.
- [ ] Notify customer when supplier ships/delivers.
- [ ] Recompute parent order status from supplier line statuses.
- [ ] Add admin visibility into supplier fulfillment progress.

Acceptance criteria:
- Suppliers can fulfill their own orders without seeing other suppliers' data.
- Customer and admin order status remains accurate.

## Phase 9: Payments, Commission, and Settlement Readiness

- [ ] Define marketplace payment model:
  - Vortexus collects full customer payment
  - supplier payout happens later
  - Vortexus commission is deducted
- [ ] Add supplier commission settings.
- [ ] Add supplier payout account fields.
- [ ] Track payable amount per supplier order group.
- [ ] Track settlement status:
  - pending
  - payable
  - paid
  - held
  - disputed
- [ ] Add admin settlement report.
- [ ] Add supplier payout summary view.
- [ ] Ensure Pesapal payment status is confirmed before order release/fulfillment.

Acceptance criteria:
- Supplier selling can be reconciled financially.
- Payments do not create blind spots between customer order, supplier order, commission, and payout.

## Phase 10: Security and Compliance

- [ ] Add permission tests for every supplier endpoint.
- [ ] Add object-level access tests for products, orders, images, and stock records.
- [ ] Ensure suppliers cannot set unsafe product fields:
  - `is_public`
  - approval status
  - partner
  - account manager
  - search visibility
- [ ] Validate uploads for file type, size, and storage path.
- [ ] Add audit logs for supplier profile, product, order, and payout changes.
- [ ] Add rate limits for product upload and image upload.
- [ ] Add admin-only approval permissions.
- [ ] Confirm supplier sessions use existing account security controls.

Acceptance criteria:
- Supplier isolation is enforced in backend tests.
- Suppliers cannot self-approve, impersonate partners, or publish unreviewed products.

## Phase 11: Notifications

- [x] Supplier application submitted email.
- [x] Supplier approved email.
- [x] Supplier rejected email.
- [ ] More information requested email.
- [ ] Product submitted email to account manager.
- [ ] Product approved email to supplier.
- [ ] Product rejected/changes requested email to supplier.
- [ ] New supplier order email.
- [ ] Supplier fulfillment update email to customer.
- [ ] Settlement/payout notification email.

Acceptance criteria:
- Every major supplier lifecycle event has a clear notification.
- Emails are logged and retryable through existing email log tooling.

## Phase 12: Admin Reporting and Monitoring

- [ ] Supplier count by status.
- [ ] Product count by moderation status.
- [ ] Products pending approval by account manager.
- [ ] Supplier sales by period.
- [ ] Supplier fulfillment SLA report.
- [ ] Supplier cancellation/rejection rate.
- [ ] Settlement report.
- [ ] Audit log filters for supplier events.

Acceptance criteria:
- Admin can monitor marketplace health from the dashboard.

## Phase 13: End-to-End QA

- [ ] Customer applies as supplier.
- [ ] Admin reviews and approves supplier.
- [ ] Supplier logs into supplier portal.
- [ ] Supplier uploads draft product.
- [ ] Supplier submits product for review.
- [ ] Admin requests changes.
- [ ] Supplier edits and resubmits.
- [ ] Admin approves product.
- [ ] Product appears in category page, brand page, search, and photo search.
- [ ] Customer adds product to cart and checks out.
- [ ] Payment succeeds through Pesapal.
- [ ] Supplier sees assigned order.
- [ ] Supplier marks line shipped with tracking.
- [ ] Customer gets update.
- [ ] Admin sees complete audit trail.

Acceptance criteria:
- The full supplier-to-sale journey works without manual database intervention.

## Suggested Implementation Order

1. Supplier product approval model and backend permissions.
2. Admin moderation queue.
3. Supplier product status visibility and upload UI.
4. Storefront/search filtering to hide unapproved products.
5. Supplier portal access states for pending, approved, suspended.
6. Order fulfillment hardening.
7. Notifications.
8. Commission/settlement reporting.
9. Full security test suite.
10. End-to-end QA and production readiness review.
