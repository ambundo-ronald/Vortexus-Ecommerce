# Oscar Dashboard Gap Tasks

This backlog tracks the missing dashboard coverage compared with Oscar's built-in `/dashboard/`. Work these tasks one by one, in priority order.

## Priority 1: Catalog Foundation

### Task 1: Catalog Categories - Done
- Build `/catalog/categories` page.
- Add create/edit/delete category forms.
- Support parent/child category browsing.
- Wire to `/admin/catalog/categories/`, `/admin/catalog/categories/{id}/`, and `/admin/catalog/categories/{id}/children/`.
- Done when staff can manage the category tree without using Oscar dashboard.
- Completed in `Dashboard/app/pages/catalog/categories.vue`.
- Added `Dashboard/app/composables/useCategories.ts` for category API access.
- Added sidebar navigation entry for `/catalog/categories`.
- Updated backend API docs for the admin category endpoints.
- Verified with `npm.cmd run build`.

### Task 2: Product Types - Done
- Build `/catalog/product-types` page.
- Add create/edit/delete product type forms.
- Wire to `/admin/catalog/product-types/` and `/admin/catalog/product-types/{id}/`.
- Done when product types/classes can be managed from the Nuxt dashboard.
- Completed in `Dashboard/app/pages/catalog/product-types.vue`.
- Added `Dashboard/app/composables/useProductTypes.ts` for product type API access.
- Added sidebar navigation entry for `/catalog/product-types`.
- Updated backend API docs for the admin product type endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 3: Product Attributes - Done
- Build `/catalog/attributes` page.
- Add create/edit/delete attribute forms.
- Connect attributes to product type workflows where the API supports it.
- Wire to `/admin/catalog/attributes/` and `/admin/catalog/attributes/{id}/`.
- Done when staff can manage reusable catalog attributes.
- Completed in `Dashboard/app/pages/catalog/attributes.vue`.
- Added `Dashboard/app/composables/useAttributes.ts` for attribute API access.
- Added product type selector using `useProductTypes`.
- Added sidebar navigation entry for `/catalog/attributes`.
- Updated backend API docs for the admin attribute endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 4: Product Options - Done
- Build `/catalog/options` page.
- Add create/edit/delete option forms.
- Wire to `/admin/catalog/options/` and `/admin/catalog/options/{id}/`.
- Done when product options are manageable from the Nuxt dashboard.
- Completed in `Dashboard/app/pages/catalog/options.vue`.
- Added `Dashboard/app/composables/useOptions.ts` for option API access.
- Added sidebar navigation entry for `/catalog/options`.
- Updated backend API docs for the admin option endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 5: Stock Alerts - Done
- Build `/catalog/stock-alerts` page.
- Add filters for status, product, and customer where available.
- Add view/update/delete actions.
- Wire to `/admin/catalog/stock-alerts/` and `/admin/catalog/stock-alerts/{id}/`.
- Done when staff can review and resolve product stock alerts.
- Completed in `Dashboard/app/pages/catalog/stock-alerts.vue`.
- Added `Dashboard/app/composables/useStockAlerts.ts` for stock alert API access.
- Added search, status filtering, detail view, close/reopen actions, and stock alert KPI cards.
- Added sidebar navigation entry for `/catalog/stock-alerts`.
- Updated backend API docs for the admin stock alert endpoints.
- Note: the current backend supports status updates but does not expose a stock alert delete endpoint.
- Verified with `npm.cmd run build` and backend `manage.py check`.

## Priority 2: Promotions And Merchandising

### Task 6: Offers - Done
- Build `/promotions/offers` page.
- Add offer create/edit/detail/status workflows.
- Include condition and benefit management.
- Wire to `/admin/offers/`, `/admin/offers/{id}/`, `/admin/offers/{id}/status/`, `/admin/offers/meta/`, `/admin/offers/conditions/`, and `/admin/offers/benefits/`.
- Done when staff can manage Oscar offers without switching dashboards.
- Completed in `Dashboard/app/pages/promotions/offers.vue`.
- Added `Dashboard/app/composables/useOffers.ts` for offer, condition, benefit, metadata, and status API access.
- Added create/edit/detail/delete workflows for offers, plus status update actions.
- Added condition and benefit management tabs with create/edit/delete workflows.
- Added sidebar navigation entry for `/promotions/offers`.
- Updated backend offer create/update support for exclusivity, schedules, condition, and benefit assignment.
- Updated backend API docs for offer metadata, condition, benefit, offer, and offer status endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 7: Vouchers - Done
- Build `/promotions/vouchers` page.
- Add create/edit/detail/delete voucher workflows.
- Show voucher stats.
- Wire to `/admin/vouchers/`, `/admin/vouchers/{id}/`, `/admin/vouchers/{id}/stats/`, and `/admin/vouchers/{id}/offers/`.
- Done when staff can create and monitor vouchers.
- Completed in `Dashboard/app/pages/promotions/vouchers.vue`.
- Added `Dashboard/app/composables/useVouchers.ts` for voucher CRUD, stats, and offer linking API access.
- Added voucher search, usage/state filters, KPI cards, detail/stats view, and attach/remove offer workflows.
- Added sidebar navigation entry for `/promotions/vouchers`.
- Updated backend API docs for voucher, voucher stats, and voucher offer-link endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 8: Ranges - Done
- Build `/promotions/ranges` page.
- Add create/edit/delete range workflows.
- Add product assignment management.
- Wire to `/admin/ranges/`, `/admin/ranges/{id}/`, and `/admin/ranges/{id}/products/`.
- Done when staff can manage featured product collections.
- Completed in `Dashboard/app/pages/promotions/ranges.vue`.
- Added `Dashboard/app/composables/useRanges.ts` for range CRUD and product assignment API access.
- Added range search, visibility/scope filters, KPI cards, create/edit/delete workflows, and product add/remove assignment panel.
- Added sidebar navigation entry for `/promotions/ranges`.
- Updated backend API docs for range and range product assignment endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 9: Review Moderation - Done
- Build `/reviews` page.
- Add filters by status, product, rating, and date where available.
- Add moderation/edit/delete actions.
- Wire to `/admin/reviews/` and `/admin/reviews/{id}/`.
- Done when staff can moderate product reviews from the Nuxt dashboard.
- Completed in `Dashboard/app/pages/reviews.vue`.
- Added `Dashboard/app/composables/useReviews.ts` for admin review list, moderation update, edit, and delete API access.
- Added review search, status/rating/date filters, KPI cards, detail view, approve/reject actions, edit form, and delete confirmation.
- Added sidebar navigation entry for `/reviews`.
- Updated backend API docs for admin review list/detail/update/delete endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

## Priority 3: Operations

### Task 10: Partners And Suppliers - Done
- Build `/partners` page.
- Add create/edit/detail/delete partner workflows.
- Add partner user linking and unlinking.
- Wire to `/admin/partners/`, `/admin/partners/{id}/`, `/admin/partners/{id}/users/`, `/admin/partners/{id}/users/{user_id}/link/`, and `/admin/partners/{id}/users/{user_id}/unlink/`.
- Done when partner and supplier relationships can be managed in Nuxt.
- Completed in `Dashboard/app/pages/partners.vue`.
- Added `Dashboard/app/composables/usePartners.ts` for partner CRUD and partner-user link/unlink API access.
- Added partner search, KPI cards, create/edit/delete workflows, and user link/unlink assignment panel using admin user search.
- Added sidebar navigation entry for `/partners`.
- Updated backend API docs for partner and partner-user endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 11: Supplier Admin - Done
- Build `/suppliers` page or integrate supplier management into `/partners`.
- Add supplier list/detail/update workflows.
- Wire to `/admin/suppliers/` and `/admin/suppliers/{id}/`.
- Done when staff can manage supplier profiles from the Nuxt dashboard.
- Completed in `Dashboard/app/pages/suppliers.vue`.
- Added `Dashboard/app/composables/useSuppliers.ts` for supplier list, detail, and profile/status update API access.
- Added supplier search, status filtering, KPI cards, detail panel, edit workflow, and quick approve/suspend actions.
- Added sidebar navigation entry for `/suppliers`.
- Extended backend supplier admin detail endpoint with `GET` support and editable profile-field updates.
- Updated backend API docs for supplier list, detail, and update endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 12: Shipping Methods - Done
- Build `/shipping` page.
- Add weight-based method create/edit/delete workflows.
- Add band create/edit/delete workflows inside each method.
- Wire to `/admin/shipping/weight-based/`, `/admin/shipping/weight-based/{id}/`, `/admin/shipping/weight-based/{id}/bands/`, and `/admin/shipping/weight-based/{id}/bands/{band_id}/`.
- Done when staff can manage shipping rates without Oscar dashboard.
- Completed in `Dashboard/app/pages/shipping.vue`.
- Added `Dashboard/app/composables/useShipping.ts` for weight-based method and band API access.
- Added method search, KPI cards, method create/edit/delete workflows, and nested weight-band create/edit/delete workflows.
- Added sidebar navigation entry for `/shipping`.
- Updated backend API docs for weight-based shipping method and band endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 13: Reports - Done
- Build `/reports` page.
- Add report list and report detail views.
- Add filters/export controls if supported by response data.
- Wire to `/admin/reports/` and `/admin/reports/{report_name}/`.
- Done when staff can view operational reports from Nuxt.
- Completed in `Dashboard/app/pages/reports.vue`.
- Added `Dashboard/app/composables/useReports.ts` for report list and paginated report detail API access.
- Added report selector cards, summary KPI cards, paginated table views, client-side search for loaded rows, order status breakdown, and CSV export for loaded rows.
- Added sidebar navigation entry for `/reports`.
- Updated backend API docs for operational report list and detail endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 14: Audit Logs - Done
- Build `/audit-logs` page.
- Add filters by actor, action, model, object, and date where available.
- Add detail drawer/page.
- Wire to `/admin/audit-logs/` and `/admin/audit-logs/{id}/`.
- Done when staff can inspect admin activity from Nuxt.
- Completed in `Dashboard/app/pages/audit-logs.vue`.
- Added `Dashboard/app/composables/useAuditLogs.ts` for audit log list/detail API access.
- Added search, event type, actor email, target type, target ID, request path, status, and date range filters.
- Added KPI cards, paginated audit table, and detail modal with actor, target, request, message, and metadata sections.
- Added sidebar navigation entry for `/audit-logs`.
- Extended backend audit log filtering for search text, target ID, request path, and date range.
- Updated backend API docs for audit log list/detail endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

## Priority 4: Content And Communications

### Task 15: Pages - Done
- Build `/content/pages` page.
- Add create/edit/delete page workflows.
- Wire to `/admin/pages/` and `/admin/pages/{id}/`.
- Done when staff can manage CMS pages from Nuxt.
- Completed in `Dashboard/app/pages/content/pages.vue`.
- Added `Dashboard/app/composables/usePages.ts` for CMS flat-page list, detail, create, update, and delete API access.
- Added page search, KPI cards, detail preview, create/edit modal, delete confirmation, URL normalization, and registration-required access control.
- Added sidebar navigation entry for `/content/pages`.
- Updated backend API docs for CMS page list, detail, create, update, and delete endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 16: Communications - Done
- Build `/content/communications` page.
- Add list/edit workflows for communication templates.
- Wire to `/admin/communications/` and `/admin/communications/{slug}/`.
- Done when staff can review and update customer communication templates.
- Completed in `Dashboard/app/pages/content/communications.vue`.
- Added `Dashboard/app/composables/useCommunications.ts` for communication template list, detail, and update API access.
- Added communication search, category filtering, KPI cards, detail preview, and tabbed text email, HTML email, and SMS editing.
- Added sidebar navigation entry for `/content/communications`.
- Updated backend API docs for communication template list, detail, and update endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

## Priority 5: Finish Existing Workflows

### Task 17: Order Notes And Shipping Address - Done
- Extend order detail page with notes and shipping address workflows.
- Wire to `/admin/orders/{order_number}/notes/` and `/admin/orders/{order_number}/shipping-address/`.
- Done when staff can inspect/update order notes and shipping address details.
- Completed in `Dashboard/app/pages/orders/[id].vue`.
- Extended `Dashboard/app/composables/useOrder.ts` with order note list/create and shipping address update API helpers.
- Added full shipping address edit workflow with recipient, address lines, city/state/postcode, country code, phone, and delivery notes.
- Added order note history and create-note workflow on the order detail page.
- Extended backend order detail serialization with full shipping address fields and order notes.
- Added `GET` support to `/admin/orders/{order_number}/notes/` and validation for note creation.
- Updated backend API docs for order shipping address and order notes endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 18: Order Line Detail - Done
- Add order line detail view or drawer.
- Wire to `/admin/orders/{order_number}/lines/{line_id}/`.
- Done when staff can inspect individual order line fulfilment details.
- Completed in `Dashboard/app/pages/orders/[id].vue`.
- Extended `Dashboard/app/composables/useOrder.ts` with an order-line detail API helper.
- Added a line-detail modal from each product row showing line status, quantity, UPC, partner, partner SKU, unit prices, and line totals.
- Updated backend API docs for the order line detail endpoint.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 19: User Password Reset And Alerts - Done
- Extend user detail workflow.
- Add password reset action if backend exposes it.
- Add product alert management if backend exposes or can expose admin user alert endpoints.
- Done when user support flows match Oscar dashboard coverage.
- Completed in `Dashboard/app/pages/users.vue`.
- Extended `Dashboard/app/composables/useUser.ts` with password reset token generation and user product-alert list/cancel API helpers.
- Added admin backend endpoints for password reset token generation and user product-alert list/cancel support.
- Added user editor sections for password reset support and product alert management.
- Updated backend API docs for admin user password reset and product alert endpoints.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 20: ERPNext Preview And Import
- Status: Done
- Extend integrations page with catalog preview/import actions.
- Wire to `/admin/integrations/{connection_id}/erpnext/preview/` and `/admin/integrations/{connection_id}/erpnext/import/`.
- Done when staff can test, preview, import, and sync ERPNext data from Nuxt.
- Completed in `Dashboard/app/pages/integrations.vue`.
- Extended `Dashboard/app/composables/useIntegrations.ts` with ERPNext preview and catalog import helpers.
- Added preview controls for items, stock, and prices plus configurable preview limits.
- Added catalog import action with an include-stock option and visible import summary.
- Updated backend API docs for ERPNext preview query params and import request payload.
- Verified with `npm.cmd run build` and backend `manage.py check`.

## Cross-Cutting Tasks

### Task 21: Navigation Structure
- Status: Done
- Add sidebar groups for Catalog, Promotions, Operations, Content, and Settings.
- Keep existing top-level pages discoverable.
- Done when all new pages are reachable from dashboard navigation.
- Completed in `Dashboard/app/config/navigation.ts` and `Dashboard/app/components/Layout/Sidebar.vue`.
- Reworked sidebar navigation into grouped sections: Overview, Catalog, Promotions, Operations, Content, and Settings.
- Kept all existing dashboard pages discoverable, including campaigns, analytics, media, integrations, and settings.
- No API documentation changes were needed because this task only reorganizes dashboard navigation.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 22: Shared Admin Table Pattern
- Status: Done
- Create reusable list/table controls for search, filters, sorting, pagination, empty state, loading state, and error state.
- Apply to new admin pages as they are built.
- Done when new pages do not duplicate table boilerplate.
- Added shared admin table components:
  - `Dashboard/app/components/Admin/TableToolbar.vue` for title, search, filters, refresh, and create actions.
  - `Dashboard/app/components/Admin/TableState.vue` for loading, empty, error, and table body slot rendering.
  - `Dashboard/app/components/Admin/TableFooter.vue` for result counts and optional pagination.
- Applied the pattern to catalog categories and vouchers as representative admin tables.
- No API documentation changes were needed because this task only standardizes dashboard table UI.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 23: Shared Form Pattern
- Status: Done
- Create reusable form shell and validation helpers for admin CRUD screens.
- Standardize save/cancel/delete feedback.
- Done when forms feel consistent across catalog, promotions, operations, and content pages.
- Added shared admin form components:
  - `Dashboard/app/components/Admin/FormModal.vue` for CRUD modal header, close action, validation error display, and save/cancel footer.
  - `Dashboard/app/components/Admin/ConfirmDialog.vue` for standardized delete/confirmation dialogs.
  - `Dashboard/app/composables/useAdminForm.ts` for required-field validation helpers.
- Applied the pattern to catalog categories and vouchers as representative CRUD screens.
- No API documentation changes were needed because this task only standardizes dashboard form UI.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 24: Permissions And Session Handling
- Status: Done
- Confirm every new page requires staff authentication.
- Confirm failed API requests redirect to login consistently.
- Done when direct navigation to protected pages is blocked for non-staff users.
- Confirmed dashboard routes are protected by global Nuxt auth middleware, with `/login` as the only public dashboard route.
- Confirmed new backend admin endpoints use `permissions.IsAdminUser`, including catalog, promotions, content, operations, reports, audit logs, media, settings, ERPNext integrations, and user/supplier admin routes.
- Tightened dashboard session refresh so non-staff `/account/me/` responses are not kept as authenticated dashboard state.
- Tightened API 401/403 handling so the local dashboard session is cleared before redirecting to `/login`.
- Updated API docs to state that `/api/v1/admin/` endpoints require an authenticated staff session.
- Verified with `npm.cmd run build` and backend `manage.py check`.

### Task 25: Smoke Tests
- Status: Done
- Add basic page-render or route smoke tests for each new dashboard section.
- Add API composable tests where practical.
- Done when the dashboard can be checked quickly before each merge.
- Added `npm run test:smoke` to verify dashboard section routes, navigation links, shared admin table/form helpers, and source-level auth/API session handling.
- Documented the smoke test command in the Dashboard README.

## Post-Oscar Dashboard Enhancements

### Task 26: Storefront Marketing Content
- Status: Done
- Build dashboard management for storefront banners, promo branding, hero sections, announcement strips, and featured homepage blocks.
- Add backend models/API endpoints if no existing content-block API covers this workflow.
- Support image/media selection, headline/copy, CTA text/link, placement, sort order, active status, and optional start/end dates.
- Expose storefront fetch endpoints for active marketing blocks by placement.
- Update API documentation and task completion notes when implemented.
- Done when staff can manage homepage and promotional storefront content without code changes.
- Added `apps.content.MarketingBlock` with placement, headline/copy, image URL, CTA, styling, active status, sort order, optional start/end dates, and metadata.
- Added staff endpoints at `/api/v1/admin/marketing-blocks/` and `/api/v1/admin/marketing-blocks/<block_id>/`.
- Added public storefront endpoint at `/api/v1/content/marketing-blocks/` with optional `placement` filtering for active/current blocks.
- Added dashboard page `/content/marketing-blocks` and Content navigation entry.
- Updated API documentation and dashboard smoke tests.
- Wired `frontendV1` homepage to render marketing placements from the public endpoint:
  - `announcement` above the hero.
  - `home_hero` in the hero carousel.
  - `promo_banner` below the hero.
  - `featured` as a homepage feature grid.
  - `brand_strip` near the bottom of the homepage.
- Added storefront fallback behavior so the existing static hero images still render when no dashboard marketing blocks exist.
