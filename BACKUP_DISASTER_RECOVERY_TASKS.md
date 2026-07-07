# Backup And Disaster Recovery Tasks

Goal: make sure Vortexus can recover customers, orders, payments, products, media, supplier data, and ERPNext sync state after a server failure, bad deploy, database corruption, accidental deletion, or hosting incident.

## Phase 1: Define Recovery Targets

- [ ] Set production recovery targets.
  - RPO: maximum acceptable data loss window.
  - RTO: maximum acceptable downtime before the site is usable again.
  - Recommended launch target: RPO 4 hours for database, RTO 4 hours for core storefront/admin.
- [ ] Classify critical data.
  - Critical: orders, payments, payment logs, customers, supplier records, ERPNext mapping IDs.
  - Important: products, inventory snapshots, shipping settings, marketing content.
  - Rebuildable: OpenSearch indexes, cache, temporary Celery state.
- [ ] Decide who can access backup and restore controls.
  - Recommended: superadmin only for download/restore.
  - Staff/admin can view backup status but cannot download secrets or restore live data.

## Phase 2: Backup Coverage

- [x] Back up PostgreSQL.
  - Customers, carts, orders, payments, products, suppliers, admin settings, audit logs, shipping rules.
- [x] Back up uploaded media.
  - Product images, marketing block images, supplier documents, category/brand assets.
- [ ] Back up configuration references.
  - Environment variable names and masked values.
  - Payment provider mode, ERPNext connection settings, email provider settings.
  - Do not store raw secrets inside normal downloadable backups unless encrypted.
- [x] Back up integration state.
  - ERPNext Customer, Sales Order, Sales Invoice, Payment Entry mapping IDs.
  - Sync queue status and failed sync records.
- [x] Decide OpenSearch strategy.
  - Recommended: do not back up OpenSearch as primary source.
  - Add a rebuild command that repopulates search from PostgreSQL.

## Phase 3: Backup Storage

- [ ] Choose off-server storage.
  - Recommended: S3-compatible bucket, Cloudflare R2, AWS S3, Backblaze B2, or managed database backups.
- [ ] Encrypt backups before upload.
  - Database dumps and media archives must be encrypted at rest.
- [ ] Add retention policy.
  - Hourly or 4-hour backups for 48 hours.
  - Daily backups for 30 days.
  - Monthly backups for 6-12 months.
- [ ] Add backup integrity metadata.
  - Timestamp, environment, app version/commit, database name, file size, checksum, backup type.
- [ ] Prevent local-only backups.
  - Local backup files should be temporary and cleaned after successful upload.

## Phase 4: Backend Backup Service

- [x] Add backend app/module for backup operations.
  - Suggested folder: `Backend/apps/backups/`.
- [x] Add backup models.
  - `BackupRun`: status, type, size, checksum, storage path, started/finished times, triggered_by.
  - `BackupRestoreRun`: status, source backup, restore mode, started/finished times, triggered_by.
- [x] Add backup runner service.
  - Database dump.
  - Media archive.
  - Manifest generation.
  - Encryption.
  - Upload to storage.
  - Cleanup temporary files.
- [x] Add backup verification service.
  - Check file exists in storage.
  - Validate checksum.
  - Optionally test-load dump into a temporary database in staging.
- [x] Add restore service.
  - Restore should be disabled in production by default unless explicitly unlocked.
  - Prefer restore-to-staging first, then manual promotion.

## Phase 5: Scheduled Backups

- [x] Add Celery task for scheduled database backup.
  - Recommended launch cadence: every 4 hours.
- [x] Add Celery task for scheduled media backup.
  - Recommended launch cadence: daily, or incremental if storage grows quickly.
- [x] Add Celery task for backup verification.
  - Run after every backup.
- [ ] Add failed-backup alerts.
  - Email/admin notification if latest backup fails.
  - Alert if no successful backup exists within the RPO window.
- [x] Add management commands.
  - `backup_database`
  - `backup_media`
  - `verify_backup`
  - `restore_backup`
  - `rebuild_search_index`

## Phase 6: Admin Dashboard

- [x] Add admin backup page.
  - Latest backup status.
  - Backup history.
  - Manual backup trigger.
  - Backup size/checksum/storage location.
- [x] Add role restrictions.
  - Superadmin can trigger and download.
  - Admin can view status only.
- [ ] Add restore controls carefully.
  - Restore-to-staging action first.
  - Production restore requires confirmation and maintenance mode.
- [ ] Add backup settings page.
  - Storage provider.
  - Retention policy.
  - Schedule.
  - Notification emails.
- [x] Add audit logs.
  - Backup triggered.
  - Backup downloaded.
  - Restore requested.
  - Restore completed/failed.

## Phase 7: Disaster Recovery Runbook

- [ ] Create a written recovery runbook.
  - New server setup.
  - Install Docker/app.
  - Restore database.
  - Restore media.
  - Run migrations.
  - Rebuild search index.
  - Start services.
  - Verify storefront/admin/API.
- [ ] Add payment reconciliation steps.
  - Compare local payment logs with Pesapal/M-Pesa dashboard.
  - Identify paid orders missing locally.
  - Recreate or resync affected orders.
- [ ] Add ERPNext reconciliation steps.
  - Confirm ecommerce Sales Orders, Sales Invoices, Payment Entries.
  - Retry failed sync events.
  - Prevent duplicate ERPNext records during restore.
- [ ] Add DNS/tunnel recovery steps.
  - Cloudflare records.
  - Tunnel/service tokens.
  - SSL/cert verification.
- [ ] Add admin verification checklist.
  - Log in.
  - View orders.
  - View payments.
  - View products/images.
  - Place test order.
  - Confirm ERPNext sync.

## Phase 8: Testing Before Launch

- [ ] Test manual database backup.
- [ ] Test manual media backup.
- [ ] Test scheduled backup.
- [ ] Test failed backup alert.
- [ ] Test restore into staging.
- [ ] Test search rebuild after restore.
- [ ] Test media images after restore.
- [ ] Test order/payment records after restore.
- [ ] Test ERPNext sync mappings after restore.
- [ ] Document actual recovery time.

## Phase 9: Production Hardening

- [ ] Confirm backups are not publicly accessible.
- [ ] Confirm backup downloads require strong admin authentication.
- [ ] Confirm raw `.env` files are not included in ordinary backups.
- [ ] Confirm secrets are either excluded or encrypted.
- [ ] Confirm backup storage credentials are rotated.
- [ ] Confirm old backups are deleted according to retention.
- [ ] Confirm restore cannot be triggered accidentally from admin.
- [ ] Confirm audit logs are kept for backup actions.

## Launch Priority

Must have before launch:

- [ ] Automated PostgreSQL backups to off-server storage.
- [ ] Automated media backups to off-server storage.
- [ ] Backup history visible in admin.
- [ ] Failed backup alert.
- [ ] Restore runbook tested at least once in staging.
- [x] Search rebuild command.
- [ ] Payment and ERPNext reconciliation steps.

Nice to have after launch:

- [ ] One-click admin backup download.
- [ ] Restore-to-staging button.
- [ ] Incremental media backups.
- [ ] Point-in-time database recovery.
- [ ] Backup health score on admin dashboard.
