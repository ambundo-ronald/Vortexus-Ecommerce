<script setup lang="ts">
const searchQuery = ref();
</script>

<template>
  <NuxtLayout>
    <UApp
      :toaster="{
        position: 'bottom-right',
      }"
    >
      <div class="h-auto min-h-full flex bg-elevated dark:bg-default">
        <LayoutSidebar />

        <div class="w-full">
          <div
            class="flex items-center justify-between dark:border-b border-default py-2 px-4 bg-inverted dark:bg-default fixed left-0 top-0 right-0 z-20"
          >
            <div class="flex items-center justify-between gap-2">
              <!-- Logo -->
              <NuxtLink to="/" class="flex items-center justify-start gap-1">
                <div
                  class="rounded flex items-center justify-center w-9 h-9 p-1 rounded-full"
                >
                  <img src="/logo.png" alt="" >
                </div>
                <h1
                  class="text-lg tracking-tight font-semibold text-inverted dark:text-default"
                >
                  Nuxt Charts
                </h1>
              </NuxtLink>

              <UIcon name="i-lucide-chevrons-up-down" />
            </div>

            <UInput
              v-model="searchQuery"
              variant="none"
              class="max-w-lg w-full bg-neutral-800 rounded-lg"
              size="lg"
              icon="i-lucide-search"
              placeholder="Search..."
              :ui="{ leadingIcon: 'size-4' }"
            />
            <div class="mx-4">
              <UButton icon="i-lucide-bell" class="text-inverted dark:text-default" variant="ghost" />
            </div>
          </div>
          <div class="min-h-full h-auto pt-13.5 pb-8 pl-64">
            <NuxtPage />
          </div>
        </div>
      </div>
    </UApp>
  </NuxtLayout>
</template>
