# ERP Integration Architecture

This document defines the recommended ERP integration model for Vortexus.

Goal:
- allow supplier ERP systems to integrate through APIs
- allow Vortexus to sync with ERPNext as the internal ERP backbone
- preserve marketplace performance and control over checkout, orders, and stock reservations

## 1) Executive Decision

Recommended architecture:

1. `Vortexus backend` remains the commerce and marketplace core
2. `ERPNext` acts as the internal ERP/system of record for operations
3. `Supplier ERPs` connect through APIs/connectors into Vortexus

Important constraint:
- Vortexus should not use ERPNext tables as its direct application database
- the integration must be API-based, event-based, or queue-based

This is the right tradeoff because it:
- keeps storefront performance predictable
- preserves marketplace-specific business rules
- supports multiple supplier systems
- avoids tight schema coupling to ERPNext internals

## 2) Source Of Truth

Use explicit ownership by domain.

### Vortexus owns
- marketplace customer accounts
- authentication and sessions
- carts and wishlists
- checkout
- payment sessions
- order orchestration
- stock reservations
- supplier marketplace permissions
- public product presentation layer
- reviews and storefront interaction data

### ERPNext owns
- internal operational stock
- procurement and purchasing
- warehouse master data
- internal supplier master
- accounting and invoicing if enabled
- internal product master if you choose ERP-first catalog governance

### Supplier ERP owns
- supplier-local stock balance
- supplier-local catalog fields
- supplier lead times
- supplier local warehouses
- supplier internal order fulfillment data

### Shared / synchronized
- products
- prices
- stock balances
- supplier mappings
- order and fulfillment states

## 3) Core Principle

Do not query supplier ERP or ERPNext synchronously during customer page rendering.

Instead:
1. ingest ERP data into Vortexus
2. normalize it
3. store marketplace-ready state locally
4. use Vortexus data for search, catalog, pricing, and availability
5. push orders/fulfillment events back to ERP systems asynchronously

This keeps:
- page loads fast
- availability stable
- reservations enforceable
- integrations resilient when upstream ERP is slow or offline

## 4) Recommended Integration Topology

### Hub-and-spoke model

- `ERPNext`
  - central internal ERP
- `Vortexus`
  - marketplace and ecommerce core
- `Supplier connectors`
  - one connector per supplier ERP type

### Inbound sync to Vortexus

From ERPNext and/or supplier ERPs:
- products
- product attributes
- stock balances
- warehouses
- price lists
- lead times
- supplier references

### Outbound sync from Vortexus

To ERPNext and/or supplier ERPs:
- marketplace orders
- order line allocations
- customer delivery details
- shipment status updates
- tracking numbers
- cancellation events

## 5) ERPNext Role

Recommended ERPNext role:
- internal operations master
- not direct website database

ERPNext can be the upstream source for:
- internal catalog
- your owned stock
- your own warehouses
- procurement
- central supplier records

Vortexus then consumes ERPNext data and presents it in marketplace-friendly form.

## 6) Supplier ERP Integration Model

Each supplier should be treated as an integration tenant.

Per supplier we should store:
- supplier profile
- integration type
- endpoint/base URL
- auth credentials reference
- sync mode
- field mappings
- product mapping table
- warehouse mapping table
- customer/export rules
- last sync timestamps
- integration status

Supported sync modes:

1. `Webhook-first`
- best for stock and fulfillment updates
- near real-time

2. `Polling`
- fallback when supplier ERP has no webhook capability
- recommended for:
  - products
  - prices
  - stock snapshots

3. `Batch file`
- CSV/SFTP fallback for suppliers with weak ERP API support

## 7) Customer Data Rule

Do not import supplier ERP customers into Vortexus as marketplace customers by default.

Recommended rule:
- Vortexus customer is the master customer identity
- when a marketplace order is routed to a supplier, Vortexus sends the customer snapshot needed for fulfillment

That includes:
- delivery contact name
- delivery phone
- shipping address
- company name if present
- order reference

Why:
- avoids customer duplication
- avoids ownership confusion
- protects customer privacy scope
- keeps marketplace identity consistent

## 8) Real-Time Stock Strategy

Yes, real-time stock is achievable, but it should be implemented as synchronized availability, not live ERP reads per request.

Recommended stock model:

1. supplier ERP pushes stock updates to Vortexus by webhook where possible
2. otherwise Vortexus polls supplier ERP at interval
3. Vortexus stores supplier stock locally
4. Vortexus applies:
   - reservations
   - oversell protection
   - checkout validation
5. fulfillment/ship events reduce or reconcile stock back through the sync loop

Recommended freshness targets:
- stock: 1 to 5 minutes for polling suppliers
- products/prices: 15 to 60 minutes
- orders: immediate outbound
- fulfillment updates: immediate inbound if webhook-capable

## 9) Data Objects To Sync

### Products
- external ERP product id
- supplier product id
- title
- description
- category
- brand
- ERP attributes
- image references
- active/inactive status

### Prices
- base price
- currency
- customer group price if needed
- MOQ
- lead-time-dependent price if needed

### Stock
- warehouse id
- available quantity
- reserved quantity if supplier ERP exposes it
- reorder threshold
- backorder flag
- lead time
- last updated timestamp

### Customers
Use carefully.

Recommended scope:
- outbound order customer snapshot
- optional B2B account mapping when a supplier requires customer account creation in ERP

### Orders
- marketplace order header
- supplier order group
- order lines
- tax/shipping summary
- customer delivery snapshot
- payment state where relevant

### Fulfillment
- packed
- shipped
- delivered
- cancelled
- tracking reference
- dispatch date
- warehouse source

## 10) Proposed Internal Components

Recommended future app:

```text
apps/integrations
```

Suggested subdomains:
- `models.py`
  - integration connections
  - sync jobs
  - sync logs
  - mapping tables
- `services/`
  - ERPNext adapter
  - generic REST adapter
  - supplier adapter registry
- `tasks.py`
  - polling
  - import jobs
  - export jobs
  - retries
- `api/`
  - webhook receivers
  - supplier push endpoints
  - integration admin endpoints

## 11) Proposed Core Models

These are the main tables I recommend when implementation starts.

### IntegrationConnection
- `id`
- `partner`
- `connection_type`
  - `erpnext`
  - `rest`
  - `csv`
  - `sftp`
- `base_url`
- `auth_type`
- `credential_ref`
- `status`
- `is_active`
- `poll_interval_minutes`
- `last_successful_sync_at`
- `last_failed_sync_at`

### IntegrationMapping
- `id`
- `connection`
- `entity_type`
  - `product`
  - `warehouse`
  - `customer`
  - `order`
- `external_id`
- `internal_id`
- `internal_model`
- `metadata`

### SyncJob
- `id`
- `connection`
- `job_type`
  - `products_import`
  - `stock_import`
  - `price_import`
  - `order_export`
  - `fulfillment_import`
- `status`
- `started_at`
- `finished_at`
- `cursor`
- `summary`

### SyncEventLog
- `id`
- `connection`
- `direction`
  - `inbound`
  - `outbound`
- `entity_type`
- `external_reference`
- `status`
- `payload_excerpt`
- `error_message`
- `created_at`

## 12) Proposed API Surface

### Supplier push endpoints

These should be supplier-specific authenticated endpoints.

- `POST /api/v1/integrations/suppliers/<partner_id>/products/sync/`
- `POST /api/v1/integrations/suppliers/<partner_id>/stock/sync/`
- `POST /api/v1/integrations/suppliers/<partner_id>/prices/sync/`
- `POST /api/v1/integrations/suppliers/<partner_id>/fulfillment/sync/`

### Integration admin endpoints

- `GET /api/v1/admin/integrations/`
- `POST /api/v1/admin/integrations/`
- `PATCH /api/v1/admin/integrations/<id>/`
- `POST /api/v1/admin/integrations/<id>/sync/`
- `GET /api/v1/admin/integrations/<id>/logs/`

### ERPNext-specific endpoints

These may be internal-only or worker-driven:

- import items
- import stock ledger / balance
- import price lists
- export marketplace orders
- import delivery notes / shipment status

## 13) Security Requirements

Required controls:
- per-connection API keys or signed webhook secrets
- IP allowlisting where possible
- payload signature validation
- audit logging for every inbound/outbound integration action
- rate limiting on inbound sync endpoints
- idempotency keys on sync payloads
- secret storage outside plain code

Do not:
- expose supplier ERP credentials to frontend
- let supplier integrations write directly into marketplace-critical tables without validation
- trust supplier payloads for customer identity ownership

## 14) Conflict Resolution Rules

Define explicit rules before implementation.

Recommended defaults:

### Product metadata
- ERPNext wins for your house-owned catalog
- supplier ERP wins for supplier-owned offer metadata

### Stock
- latest successful supplier stock snapshot wins for supplier-owned offers
- Vortexus reservation logic still subtracts locally-reserved amounts for sellable availability

### Price
- supplier ERP or ERPNext price list wins depending on ownership
- storefront promotions remain Vortexus concern

### Order status
- Vortexus is authoritative for customer-visible marketplace order status
- supplier ERP updates supplier fulfillment state
- Vortexus maps supplier fulfillment state into marketplace-visible status

## 15) Recommended Rollout

### Phase 1: ERP foundation
- create `integrations` app
- add integration connection models
- add sync logs and mapping tables
- add ERPNext connection model

### Phase 2: ERPNext internal sync
- import products
- import stock
- import prices
- export marketplace orders into ERPNext

### Phase 3: Supplier ERP sync
- supplier product sync endpoint
- supplier stock sync endpoint
- supplier fulfillment sync endpoint

### Phase 4: Webhooks and real-time behavior
- webhook verification
- near-real-time stock updates
- automatic fulfillment propagation

### Phase 5: Operational tooling
- admin integration dashboard
- retry/replay controls
- sync health reporting

## 16) ERPNext-First Recommendation

If you want one clear recommendation:

Use ERPNext as your internal ERP master and integrate Vortexus with it through APIs.

Then allow suppliers to connect their own ERPs into Vortexus through a standardized integration layer.

That gives you:
- central operational control
- support for multi-supplier marketplace growth
- real-time or near-real-time stock
- safer long-term architecture than direct DB coupling

## 17) Next Implementation Step

When you are ready to build this, the first concrete task should be:

1. create `apps/integrations`
2. add connection + mapping + sync log models
3. implement ERPNext connector first
4. implement supplier stock sync endpoint second

This order gives the fastest path to real stock synchronization without destabilizing the marketplace core.
