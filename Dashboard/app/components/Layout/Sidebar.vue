<script setup lang="ts">
import { navSections, supportNav } from '~/config/navigation'

const route = useRoute()

const isLinkActive = (item: { to?: string }) => {
  if (!item.to)
    return false
  if (item.to === '/')
    return route.path === '/'
  return route.path.startsWith(item.to)
}
</script>

<template>
  <div
    class="fixed bottom-0 left-0 top-0 hidden min-h-screen w-64 flex-col overflow-y-auto border-r border-slate-200 bg-white p-4 lg:flex dark:border-slate-800 dark:bg-slate-950"
  >
    <NuxtLink to="/" class="mb-8 flex items-center gap-3">
      <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#255be8] text-base font-black text-white">
        RM
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
      <section v-for="section in navSections" :key="section.label" class="space-y-2">
        <div class="text-xs font-bold uppercase tracking-wide text-slate-400">
          {{ section.label }}
        </div>
        <div class="w-full space-y-1">
          <NuxtLink v-for="item in section.items" :key="item.label" :to="item.to" block>
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
        <NuxtLink v-if="item.to" :to="item.to">
          <UButton
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            :icon="item.icon"
          >
            {{ item.label }}
            <span
              v-if="item.highlight"
              class="ml-auto h-1.5 w-1.5 rounded-full bg-[#3d7cff]"
            />
          </UButton>
        </NuxtLink>
      </template>

    </div>
  </div>
</template>
