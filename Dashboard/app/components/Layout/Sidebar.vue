<script setup lang="ts">
import { mainNav, supportNav, settingsNav } from '~/config/navigation';

const route = useRoute();

const isLinkActive = (item: { to?: string }) => {
  if (!item.to) return false;
  if (item.to === '/') return route.path === '/';
  return route.path.startsWith(item.to);
};
</script>

<template>
  <div
    class="hidden lg:flex w-64 min-h-screen fixed left-0 top-0 bottom-0 overflow-y-auto p-4 flex-col bg-white border-r border-slate-200"
  >
    <NuxtLink to="/" class="mb-8 flex items-center gap-3">
      <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#255be8] text-base font-black text-white">
        VX
      </div>
      <div>
        <p class="text-lg font-black leading-tight text-slate-950">
          Vortexus
        </p>
        <p class="text-xs text-slate-500">
          Operations
        </p>
      </div>
    </NuxtLink>

    <nav class="space-y-2">
      <div class="text-xs font-bold uppercase tracking-wide text-slate-400">
        Manage
      </div>
      <div class="w-full space-y-1">
        <template v-for="item in mainNav" :key="item.label">
          <NuxtLink v-if="item.to" :to="item.to" block>
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
          <UButton
            v-else
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            :icon="item.icon"
          >
            {{ item.label }}
          </UButton>
        </template>
      </div>
    </nav>
    <div class="mt-auto">
      <h3 class="text-xs font-bold mb-2 uppercase tracking-wide text-slate-400">
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
      <div class="mt-6 border-t pt-4 border-slate-200">
        <h3 class="text-xs font-bold mb-2 uppercase tracking-wide text-slate-400">
          Settings
        </h3>
        <template v-for="item in settingsNav" :key="item.label">
          <NuxtLink v-if="item.to" :to="item.to">
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
        </template>
      </div>
    </div>
  </div>
</template>
