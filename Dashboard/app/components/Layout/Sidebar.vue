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
  if (item.to === '/')
    return route.path === '/'
  return route.path.startsWith(item.to)
}

const visibleNavSections = computed(() => {
  if (auth.isPlatformAdmin.value)
    return navSections
  if (auth.isAccountManager.value)
    return accountManagerNavSections
  return supplierNavSections
})
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

    <nav class="space-y-6">
      <section v-for="section in visibleNavSections" :key="section.label" class="space-y-2">
        <div class="text-xs font-bold uppercase tracking-wide text-slate-400">
          {{ section.label }}
        </div>
        <div class="w-full space-y-1">
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
