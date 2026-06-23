# Vortexus k6 load tests

This suite tests the Django API used by `frontendV1`. It separates read-heavy
storefront traffic from cart, account, and checkout traffic so bottlenecks are
easy to identify.

## Scripts

| Script | Purpose | Writes data |
| --- | --- | --- |
| `scripts/smoke.js` | One complete public browse plus cart add/remove | Temporary cart line |
| `scripts/public-load.js` | Expected storefront browsing load | No |
| `scripts/cart-load.js` | Anonymous session cart writes | Temporary cart lines |
| `scripts/account-load.js` | Login and authenticated account reads | Login sessions only |
| `scripts/checkout-preview.js` | Cart, shipping address/method, preview | Temporary cart/session data |
| `scripts/mixed-load.js` | Concurrent browsing, cart, and optional account traffic | Temporary cart/session data |
| `scripts/stress.js` | Find the gradual breaking point | No |
| `scripts/spike.js` | Test sudden traffic jumps and recovery | No |
| `scripts/soak.js` | Find leaks and degradation over time | No |

No script creates an order, initializes a payment, or sends a checkout
confirmation email.

## Prerequisites

Start PostgreSQL, Redis, and OpenSearch:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/Backend
docker compose up -d postgres redis opensearch
```

Install the backend requirements before a capacity test. Gunicorn is declared
in `Backend/requirements.txt`:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/Backend
source .venv/bin/activate
pip install -r requirements.txt
```

Then run Django with the dedicated settings and Gunicorn:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/Backend
DJANGO_SETTINGS_MODULE=config.settings.performance \
./.venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120
```

The dedicated `config.settings.performance` module raises API throttle limits
and uses an in-memory email backend. Normal local and production limits are not
changed. Never run stress or spike tests against production without a
maintenance window and explicit approval.

For smoke-test validation only, `runserver` can be used:

```bash
./.venv/bin/python manage.py runserver 127.0.0.1:8000 \
  --settings=config.settings.performance \
  --noreload
```

Do not use `runserver` to decide production capacity. It does not represent a
multi-worker deployment.

If the normal development backend is already using port `8000`, leave it
running and start the performance backend on `8001`:

```bash
./.venv/bin/python manage.py runserver 127.0.0.1:8001 \
  --settings=config.settings.performance \
  --noreload
```

Point k6 at that isolated process:

```bash
k6 run -e BASE_URL=http://127.0.0.1:8001 scripts/smoke.js
```

Confirm the performance settings before starting k6:

```bash
DJANGO_SETTINGS_MODULE=config.settings.performance \
./.venv/bin/python manage.py shell -c \
"from django.conf import settings; print(settings.SETTINGS_MODULE); print(settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['public_search'])"
```

Expected output:

```text
config.settings.performance
1000000/hour
```

## Install or run k6

If `k6` is installed locally:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/load-tests
k6 version
```

Alternatively, run the official Docker image:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/load-tests
docker run --rm --network host \
  -v "$PWD:/scripts" \
  -w /scripts \
  grafana/k6 run scripts/smoke.js
```

## Execution order

Run the smoke test first:

```bash
cd /home/newtonmanyisa/Vortexus-Ecommerce/load-tests
k6 run scripts/smoke.js
```

Ramp public traffic progressively:

```bash
k6 run -e VUS=5 scripts/public-load.js
k6 run -e VUS=25 scripts/public-load.js
k6 run -e VUS=50 scripts/public-load.js
k6 run -e VUS=100 scripts/public-load.js
```

Run cart traffic separately:

```bash
k6 run -e VUS=20 -e DURATION=2m scripts/cart-load.js
```

Run a realistic mixed profile:

```bash
k6 run \
  -e BROWSE_VUS=40 \
  -e CART_VUS=8 \
  -e DURATION=3m \
  scripts/mixed-load.js
```

Include authenticated account traffic when dedicated users are configured:

```bash
k6 run \
  -e INCLUDE_AUTH=true \
  -e TEST_USERS_FILE=./data/users.local.json \
  -e BROWSE_VUS=40 \
  -e CART_VUS=8 \
  -e ACCOUNT_VUS=5 \
  scripts/mixed-load.js
```

For authenticated scripts, use dedicated test customers with email 2FA
disabled. Do not use administrator or real customer accounts.

Single test account:

```bash
k6 run \
  -e TEST_USER_EMAIL=loadtest@example.com \
  -e TEST_USER_PASSWORD='replace-me' \
  -e VUS=5 \
  scripts/account-load.js
```

Multiple test accounts:

```bash
cp data/users.example.json data/users.local.json
# Edit users.local.json with dedicated test credentials.
k6 run \
  -e TEST_USERS_FILE=./data/users.local.json \
  -e VUS=10 \
  scripts/account-load.js
```

Checkout preview, without placing orders:

```bash
k6 run \
  -e TEST_USERS_FILE=./data/users.local.json \
  -e VUS=5 \
  -e DURATION=1m \
  scripts/checkout-preview.js
```

Capacity tests:

```bash
k6 run -e VUS=100 scripts/stress.js
k6 run -e VUS=200 scripts/stress.js
k6 run -e VUS=400 scripts/stress.js
k6 run -e VUS=250 scripts/spike.js
k6 run -e VUS=500 scripts/spike.js
k6 run -e VUS=50 -e DURATION=2h scripts/soak.js
```

Stop increasing VUs when latency, failure, throttling, CPU, memory, database
connections, or business correctness crosses the agreed limit.

Override the API target when needed:

```bash
k6 run \
  -e BASE_URL=https://staging.example.com \
  scripts/public-load.js
```

`BASE_URL` accepts either the server root or the full `/api/v1` URL.

## Reading the output

Each run prints:

- total requests and requests per second
- p95 and p99 response latency
- HTTP failure rate
- check pass rate
- application/business error rate
- throttle (`429`) rate

Each script also writes a detailed JSON summary to `results/`, for example:

```text
results/public-load-summary.json
```

To retain every request sample as JSON:

```bash
k6 run \
  --out json=results/public-load-samples.json \
  scripts/public-load.js
```

Initial acceptance targets are:

- p95 below `800 ms` under expected load
- p99 below `1500 ms`
- HTTP failures below `1%`
- checks above `99%`
- business errors and throttling below `1%`

Stress and spike scripts allow up to `5%` failures while locating the breaking
point. Watch the backend simultaneously:

```bash
docker stats
docker compose logs -f postgres redis opensearch
```

Also monitor Gunicorn logs, PostgreSQL connections, Redis memory, OpenSearch
health, CPU, RAM, and response latency. A high request rate is not useful if
checkout correctness, inventory reservations, or session isolation fails.

## Troubleshooting

### Mostly `429 Too Many Requests`

The backend was started with normal local or production throttle rates. All
local k6 traffic originates from one IP address, so search limits are consumed
almost immediately. Restart the load-test target with
`config.settings.performance`; do not raise production limits for this.

### `dial tcp 127.0.0.1:8000: connect: connection refused`

No API process is listening, or the API process stopped under load. Confirm the
port first:

```bash
curl -i http://127.0.0.1:8000/api/v1/health/ready/
```

Then inspect the Gunicorn/Django process, container health, memory pressure,
and kernel logs before rerunning. Requests made after the process stops are
network failures and must not be interpreted as application capacity.

### Preflight reports `404`

Use either the server root or API root:

```bash
-e BASE_URL=http://127.0.0.1:8001
# or
-e BASE_URL=http://127.0.0.1:8001/api/v1
```

The suite normalizes both forms.

## Safety notes

- Test with disposable customer accounts and test stock.
- Keep email 2FA disabled on load-test accounts.
- Use at least as many accounts as concurrent authenticated VUs where possible.
- Do not enable payment or order creation in these scripts.
- Do not commit `data/users.local.json`; it contains credentials.
