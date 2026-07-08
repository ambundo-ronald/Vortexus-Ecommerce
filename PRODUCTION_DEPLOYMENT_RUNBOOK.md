# Reesolmart Production Deployment Runbook

This runbook is the controlled routine for launching Reesolmart on the Hostinger VPS.

## Target Domains

- Storefront: `https://reesolmart.com`
- Admin dashboard: `https://reesolmart.cloud`
- API: `https://api.reesolmart.cloud`

Hostinger VPS:

- VM ID: `1804166`
- Hostname: `srv1804166.hstgr.cloud`
- IPv4: `152.239.122.161`
- Plan: KVM 8, 8 vCPU, 32 GB RAM, 400 GB disk
- OS: Ubuntu 24.04 LTS

## DNS Checklist

`reesolmart.com` is hosted at Safaricom. Its `A` record should point to:

```text
152.239.122.161
```

`reesolmart.cloud` is hosted at Hostinger. Required DNS records:

```text
@    A    152.239.122.161
api  A    152.239.122.161
www  CNAME reesolmart.cloud.
```

Current observed Hostinger DNS before launch cleanup:

```text
@    A      2.57.91.91
www  CNAME  reesolmart.cloud.
```

So `reesolmart.cloud` must be repointed to the VPS, and `api.reesolmart.cloud` must be created.

## Production Cleanup Policy

For launch, production starts with an empty dashboard and only this admin user:

```text
norwaengineering8@gmail.com
```

The cleanup removes:

- all users except `norwaengineering8@gmail.com`
- orders, order lines, order notes, supplier order groups
- baskets, basket lines, wishlists, saved items
- payment sessions and payment events
- audit logs, search analytics, integration sync jobs and event logs
- notifications and push subscriptions
- supplier profiles and supplier submissions
- products, stock records, product images, categories, product attributes, product classes
- marketing blocks/media records
- payment provider configuration
- email SMTP configuration and email suppressions
- ERPNext integration connections and mappings
- admin-created shipping methods, distance delivery methods, and route cache
- OpenSearch product and image-search index documents

The cleanup preserves:

- the admin user `norwaengineering8@gmail.com`
- database schema/migrations
- Docker volumes
- backup files on disk

## Clean-Start Command

Dry-run first:

```bash
docker compose --env-file .env.production exec backend \
  python manage.py production_clean_start \
  --admin-email norwaengineering8@gmail.com
```

Execute cleanup:

```bash
docker compose --env-file .env.production exec backend \
  python manage.py production_clean_start \
  --execute \
  --admin-email norwaengineering8@gmail.com
```

This keeps the current password for `norwaengineering8@gmail.com`.

Optional: also delete backup/restore run records from the admin backup page:

```bash
docker compose --env-file .env.production exec backend \
  python manage.py production_clean_start \
  --execute \
  --admin-email norwaengineering8@gmail.com \
  --purge-backup-records
```

## Deployment Routine

Recommended manual deployment routine for launch:

1. Push verified code to GitHub `main`.
2. SSH into the VPS.
3. Pull latest code:

```bash
cd ~/Vortexus-Ecommerce
git pull origin main
```

4. Confirm `.env.production` exists and contains production values.
5. Build app images:

```bash
docker compose --env-file .env.production build backend celery-worker celery-beat frontend dashboard
```

6. Start/recreate services:

```bash
docker compose --env-file .env.production up -d
```

7. Run migrations:

```bash
docker compose --env-file .env.production exec backend python manage.py migrate
```

8. Collect static:

```bash
docker compose --env-file .env.production exec backend python manage.py collectstatic --noinput
```

9. Run health checks:

```bash
curl -fsS https://api.reesolmart.cloud/api/v1/health/live/
curl -I https://reesolmart.com
curl -I https://reesolmart.cloud
```

10. Run the clean-start dry-run.
11. Create a database/media backup.
12. Execute clean-start command.
13. Log in to admin as `norwaengineering8@gmail.com`.

## CI/CD Recommendation

For launch week, use manual deployment with the checklist above. It is safer while DNS, payment, backup, and clean-start steps are still being finalized.

After launch stabilizes, add GitHub Actions:

- run frontend build
- run backend checks/tests
- build Docker images
- SSH to VPS
- pull latest `main`
- run `docker compose build`
- run migrations
- restart services
- run health checks

Do not automate destructive cleanup in CI/CD. The clean-start command must remain a manual, explicit production operation.

## Pre-Go-Live Audit Checklist

- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS` includes `api.reesolmart.cloud`, `reesolmart.cloud`, `reesolmart.com`
- CORS allows storefront/admin domains only
- CSRF trusted origins include all HTTPS production domains
- Caddy routes:
  - `reesolmart.com` -> frontend
  - `reesolmart.cloud` -> dashboard
  - `api.reesolmart.cloud` -> backend
- Pesapal production credentials and callback URLs configured
- Email SMTP test passes
- Backups can be created and downloaded
- OpenSearch is healthy
- Postgres volume is persistent
- Backend media volume is persistent
- Admin login works
- Storefront checkout health path works
- No real secrets are committed to GitHub
