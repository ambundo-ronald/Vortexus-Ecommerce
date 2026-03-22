<script setup lang="ts">
import { ref } from "vue";
import { mainNav, supportNav, settingsNav } from '~/config/navigation';

const route = useRoute();

const collapsed = ref(false);

const isLinkActive = (item: { to?: string }) => {
  if (!item.to) return false;
  if (item.to === '/') return route.path === '/';
  return route.path.startsWith(item.to);
};
</script>

<template>
  <div
    class="w-64 h-auto min-h-full fixed  left-0 top-0 pt-22 bottom-0 overflow-y-auto p-4 flex flex-col bg-default border-r border-default"
  >
    <nav class="space-y-2">
      <div
        class="flex items-center justify-between cursor-pointer"
        @click="collapsed = !collapsed"
      >
        <div class="text-xs font-bold text-muted">NUXTCHARTS.COM</div>
        <UIcon
          :name="collapsed ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
          class="text-muted"
          size="16"
        />
      </div>
      <div v-show="!collapsed" class="w-full">
        <template v-for="item in mainNav" :key="item.label">
          <NuxtLink v-if="item.to" :to="item.to" block>
            <UButton
              variant="link"
              :active="isLinkActive(item)"
              active-variant="soft"
              class="w-full flex items-center"
              :icon="item.icon"
            >
              {{ item.label }}
              <span v-if="false" class="ml-auto text-blue-600">•</span>
            </UButton>
          </NuxtLink>
          <UButton
            v-else
            variant="link"
            class="w-full flex items-center"
            :icon="item.icon"
            icon-class="mr-1"
            icon-size="20"
          >
            {{ item.label }}
            <span v-if="false" class="ml-auto text-blue-600">•</span>
          </UButton>
        </template>
      </div>
    </nav>
    <div class="mt-auto">
      <h3 class="text-xs font-semibold mb-2 uppercase text-dimmed">
        All charts
      </h3>
      <template v-for="item in supportNav" :key="item.label">
        <NuxtLink :to="item.to">
          <UButton
            variant="link"
            class="w-full flex items-center"
            :icon="item.icon"
            icon-class="mr-1"
            icon-size="20"
          >
            {{ item.label }}
            <span
              v-if="item.highlight"
              class="w-1.5 h-1.5 bg-blue-500 rounded-full ml-2"
            />
          </UButton>
        </NuxtLink>
      </template>
      <div class="mt-6 border-t pt-4 border-muted">
        <h3 class="text-xs font-semibold mb-2 uppercase text-dimmed">
          Settings
        </h3>
        <template v-for="item in settingsNav" :key="item.label">
          <NuxtLink :to="item.to">
            <UButton
              variant="link"
              :active="isLinkActive(item)"
              active-variant="soft"
              class="w-full flex items-center"
              :icon="item.icon"
              icon-class="mr-1"
              icon-size="20"
            >
              {{ item.label }}
            </UButton>
          </NuxtLink>
        </template>
      </div>
      <UButton
        color="neutral"
        variant="soft"
        class="w-full flex items-center justify-center mt-4"
        icon="i-lucide-plus"
        icon-class="h-4 w-4"
      >
        <span>New dashboard</span>
      </UButton>
    </div>
  </div>
</template>
