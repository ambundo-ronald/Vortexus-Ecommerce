<script setup lang="ts">
const route = useRoute()
const auth = useAuth()
const colorMode = useColorMode()
const searchQuery = ref('')

colorMode.preference = 'light'
colorMode.value = 'light'

const isAuthPage = computed(() => route.path === '/login')
const displayName = computed(() => {
  const name = auth.user.value?.full_name || [auth.user.value?.first_name, auth.user.value?.last_name].filter(Boolean).join(' ')
  return name || auth.user.value?.email || 'Admin'
})

async function handleLogout() {
  await auth.logout()
}
</script>

<template>
  <UApp
    :toaster="{
      position: 'bottom-right',
    }"
  >
    <NuxtPage v-if="isAuthPage" />

    <div v-else class="min-h-screen bg-slate-50 text-slate-950">
      <LayoutSidebar />

      <div class="min-h-screen lg:pl-64">
        <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div class="flex h-18 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <NuxtLink to="/" class="flex items-center gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#255be8] text-base font-black text-white">
                VX
              </div>
              <div>
                <p class="text-lg font-black leading-tight">
                  Vortexus
                </p>
                <p class="text-xs text-slate-500">
                  Admin dashboard
                </p>
              </div>
            </NuxtLink>

            <UInput
              v-model="searchQuery"
              class="hidden max-w-xl flex-1 md:block"
              color="neutral"
              variant="outline"
              size="lg"
              icon="i-lucide-search"
              placeholder="Search dashboard..."
            />

            <div class="flex items-center gap-2">
              <UButton icon="i-lucide-bell" color="neutral" variant="ghost" />
              <UDropdownMenu
                :items="[
                  [{ label: displayName, icon: 'i-lucide-user', disabled: true }],
                  [{ label: 'Sign out', icon: 'i-lucide-log-out', onSelect: handleLogout }],
                ]"
              >
                <UButton color="neutral" variant="soft" trailing-icon="i-lucide-chevron-down">
                  <span class="hidden sm:inline">{{ displayName }}</span>
                  <span class="sm:hidden">Account</span>
                </UButton>
              </UDropdownMenu>
            </div>
          </div>
        </header>

        <main class="px-4 py-6 sm:px-6 lg:px-8">
          <NuxtLayout>
            <NuxtPage />
          </NuxtLayout>
        </main>
      </div>
    </div>
  </UApp>
</template>
