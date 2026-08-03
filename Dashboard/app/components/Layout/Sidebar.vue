<script setup lang="ts">
import { accountManagerNavSections, navSections, supplierNavSections, supportNav } from '~/config/navigation'

const route = useRoute()
const auth = useAuth()
const props = withDefaults(defineProps<{
  mobile?: boolean
}>(), {
  mobile: false,
})
const emit = defineEmits<{
  navigate: []
}>()

const isLinkActive = (item: { to?: string }) => {
  if (!item.to)
    return false
  const [itemPath, itemQuery] = item.to.split('?')
  if (itemQuery)
    return route.path === itemPath && route.fullPath.includes(`?${itemQuery}`)
  if (item.to === '/')
    return route.path === '/'
  if (item.to === '/finance')
    return route.path === '/finance' && !route.fullPath.includes('?')
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}

const visibleNavSections = computed(() => {
  if (auth.isPlatformAdmin.value)
    return navSections
  if (auth.isAccountManager.value) {
    if (!auth.canAccessFinance.value)
      return accountManagerNavSections
    return [
      ...accountManagerNavSections,
      {
        label: 'Finance',
        items: [
          {
            label: 'Overview',
            icon: 'i-lucide-layout-dashboard',
            to: '/finance',
          },
          {
            label: 'Accounting',
            icon: 'i-lucide-book-open-check',
            to: '/accounting',
          },
          {
            label: 'Payment Logs',
            icon: 'i-lucide-credit-card',
            to: '/payment-logs',
          },
          {
            label: 'Reconciliation',
            icon: 'i-lucide-shield-check',
            to: '/finance?view=reconciliation',
          },
          {
            label: 'Supplier Payables',
            icon: 'i-lucide-store',
            to: '/finance?view=supplier-payables',
          },
          {
            label: 'Payout Batches',
            icon: 'i-lucide-wallet-cards',
            to: '/finance?view=payout-batches',
          },
          {
            label: 'Refunds',
            icon: 'i-lucide-undo-2',
            to: '/finance?view=refunds',
          },
          {
            label: 'Returns',
            icon: 'i-lucide-rotate-ccw-square',
            to: '/finance?view=returns',
          },
          {
            label: 'Order Lookup',
            icon: 'i-lucide-file-search',
            to: '/finance?view=order',
          },
        ],
      },
    ]
  }
  return supplierNavSections
})

const openSections = ref<string[]>([])

const isSectionActive = (section: { items: Array<{ to?: string }> }) => section.items.some(item => isLinkActive(item))

const isSectionOpen = (label: string) => openSections.value.includes(label)

const toggleSection = (label: string) => {
  if (isSectionOpen(label)) {
    openSections.value = openSections.value.filter(sectionLabel => sectionLabel !== label)
    return
  }
  openSections.value = [...openSections.value, label]
}

watch(
  visibleNavSections,
  (sections) => {
    const activeSection = sections.find(section => isSectionActive(section))
    const initialOpenSections = activeSection ? [activeSection.label] : sections.slice(0, 1).map(section => section.label)
    openSections.value = Array.from(new Set([...openSections.value, ...initialOpenSections]))
  },
  { immediate: true },
)

watch(
  () => route.fullPath,
  () => {
    const activeSection = visibleNavSections.value.find(section => isSectionActive(section))
    if (activeSection && !isSectionOpen(activeSection.label))
      openSections.value = [...openSections.value, activeSection.label]
  },
)
</script>

<template>
  <div
    class="border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
    :class="props.mobile ? 'flex h-full w-full flex-col overflow-y-auto' : 'fixed bottom-0 left-0 top-0 hidden min-h-screen w-64 flex-col overflow-y-auto lg:flex'"
  >
    <NuxtLink
      to="/"
      class="sticky top-0 z-10 -mx-4 mb-6 flex items-center gap-3 border-b border-slate-100 bg-white px-4 pb-4 pt-1 dark:border-slate-800 dark:bg-slate-950"
      @click="emit('navigate')"
    >
      <div class="flex h-11 w-14 items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-white">
        <img src="/brand/reesolmart-logo.jpg" alt="" class="h-full w-full object-contain">
      </div>
      <div>
        <p class="text-lg font-black leading-tight text-slate-950 dark:text-slate-100">
          Reesolmart
        </p>
        <p class="text-xs text-slate-500 dark:text-slate-400">
          Just in time, buying
        </p>
      </div>
    </NuxtLink>

    <nav class="space-y-2">
      <section v-for="section in visibleNavSections" :key="section.label" class="rounded-lg">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-bold uppercase tracking-wide text-slate-500 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100"
          :class="isSectionActive(section) ? 'bg-slate-100 text-slate-950 dark:bg-slate-900 dark:text-slate-100' : ''"
          :aria-expanded="isSectionOpen(section.label)"
          @click="toggleSection(section.label)"
        >
          <span class="min-w-0 flex-1 truncate">{{ section.label }}</span>
          <span class="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-black text-slate-500 dark:bg-slate-800 dark:text-slate-300">
            {{ section.items.length }}
          </span>
          <UIcon
            name="i-lucide-chevron-down"
            class="h-4 w-4 shrink-0 transition-transform"
            :class="isSectionOpen(section.label) ? 'rotate-180' : ''"
          />
        </button>

        <div v-show="isSectionOpen(section.label)" class="mt-1 w-full space-y-1 pl-2">
          <NuxtLink v-for="item in section.items" :key="item.label" :to="item.to" block @click="emit('navigate')">
            <UButton
              color="neutral"
              variant="ghost"
              :active="isLinkActive(item)"
              active-variant="soft"
              class="w-full justify-start"
              :icon="item.icon"
            >
              {{ item.label }}
            </UButton>
          </NuxtLink>
        </div>
      </section>
    </nav>

    <div class="mt-auto">
      <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">
        Help
      </h3>
      <template v-for="item in supportNav" :key="item.label">
        <NuxtLink v-if="item.to" :to="item.to" @click="emit('navigate')">
          <UButton
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            :icon="item.icon"
          >
            {{ item.label }}
            <span
              v-if="item.highlight"
              class="ml-auto h-1.5 w-1.5 rounded-full bg-[#30328f]"
            />
          </UButton>
        </NuxtLink>
      </template>

    </div>
  </div>
</template>
