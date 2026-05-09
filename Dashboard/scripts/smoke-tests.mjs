import { existsSync, readFileSync } from 'node:fs'
import { dirname, join, normalize } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const appRoot = join(root, 'app')

const failures = []

function read(relativePath) {
  return readFileSync(join(root, relativePath), 'utf8')
}

function assert(condition, message) {
  if (!condition)
    failures.push(message)
}

function assertFile(relativePath, message = `${relativePath} exists`) {
  assert(existsSync(join(root, relativePath)), message)
}

function routeToPagePath(route) {
  if (route === '/')
    return 'app/pages/index.vue'

  const directPage = `app/pages${route}.vue`
  if (existsSync(join(root, directPage)))
    return directPage

  return `app/pages${route}/index.vue`
}

function extractNavRoutes() {
  const source = read('app/config/navigation.ts')
  return [...source.matchAll(/to:\s*['"]([^'"]+)['"]/g)].map(match => match[1])
}

function assertContains(relativePath, snippets) {
  const source = read(relativePath)

  for (const snippet of snippets)
    assert(source.includes(snippet), `${relativePath} contains ${snippet}`)
}

const requiredPages = [
  '/',
  '/analytics',
  '/products',
  '/orders',
  '/users',
  '/partners',
  '/suppliers',
  '/shipping',
  '/reports',
  '/audit-logs',
  '/media',
  '/settings',
  '/integrations',
  '/campaigns',
  '/reviews',
  '/catalog/categories',
  '/catalog/product-types',
  '/catalog/attributes',
  '/catalog/options',
  '/catalog/stock-alerts',
  '/promotions/offers',
  '/promotions/vouchers',
  '/promotions/ranges',
  '/content/pages',
  '/content/communications',
]

const navRoutes = extractNavRoutes()
for (const route of navRoutes)
  assertFile(routeToPagePath(route), `navigation route ${route} has a page file`)

for (const route of requiredPages)
  assertFile(routeToPagePath(route), `dashboard smoke route ${route} has a page file`)

const pageComposableExpectations = {
  'app/pages/catalog/categories.vue': ['useCategories', 'AdminTableToolbar', 'AdminFormModal'],
  'app/pages/catalog/product-types.vue': ['useProductTypes'],
  'app/pages/catalog/attributes.vue': ['useAttributes'],
  'app/pages/catalog/options.vue': ['useOptions'],
  'app/pages/catalog/stock-alerts.vue': ['useStockAlerts'],
  'app/pages/promotions/offers.vue': ['useOffers'],
  'app/pages/promotions/vouchers.vue': ['useVouchers', 'AdminTableToolbar', 'AdminFormModal'],
  'app/pages/promotions/ranges.vue': ['useRanges'],
  'app/pages/reviews.vue': ['useReviews'],
  'app/pages/partners.vue': ['usePartners'],
  'app/pages/suppliers.vue': ['useSuppliers'],
  'app/pages/shipping.vue': ['useShipping'],
  'app/pages/reports.vue': ['useReports'],
  'app/pages/audit-logs.vue': ['useAuditLogs'],
  'app/pages/content/pages.vue': ['usePages'],
  'app/pages/content/communications.vue': ['useCommunications'],
  'app/pages/integrations.vue': ['useIntegrations'],
  'app/pages/users.vue': ['useUser'],
}

for (const [relativePath, snippets] of Object.entries(pageComposableExpectations))
  assertContains(relativePath, snippets)

const requiredComponents = [
  'app/components/Admin/TableToolbar.vue',
  'app/components/Admin/TableState.vue',
  'app/components/Admin/TableFooter.vue',
  'app/components/Admin/FormModal.vue',
  'app/components/Admin/ConfirmDialog.vue',
  'app/composables/useAdminForm.ts',
]

for (const relativePath of requiredComponents)
  assertFile(relativePath)

assertContains('app/composables/useAdminForm.ts', [
  'export function useAdminForm',
  'firstRequiredError',
])

assertContains('app/middleware/auth.global.ts', [
  "new Set(['/login'])",
  'auth.refreshSession()',
  "navigateTo('/login')",
])

assertContains('app/composables/useAuth.ts', [
  'response.user?.is_staff ? response.user : null',
  'function clearSession()',
])

assertContains('app/composables/useBackendApi.ts', [
  '[401, 403].includes',
  'auth.clearSession()',
  "navigateTo('/login')",
])

const normalizedAppRoot = normalize(appRoot)
assert(normalizedAppRoot.endsWith(normalize('Dashboard/app')), 'smoke test paths resolve inside Dashboard/app')

if (failures.length) {
  console.error('\nDashboard smoke tests failed:')
  for (const failure of failures)
    console.error(`- ${failure}`)
  process.exit(1)
}

console.log(`Dashboard smoke tests passed (${requiredPages.length} routes, ${navRoutes.length} nav links).`)
