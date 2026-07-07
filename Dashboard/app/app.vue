<script setup lang="ts">
const route = useRoute()
const auth = useAuth()
const adminNotifications = useAdminNotifications()
const searchQuery = ref('')
const isMounted = ref(false)
let notificationTimer: ReturnType<typeof setInterval> | null = null

const isAuthPage = computed(() => route.path === '/login')
const displayName = computed(() => {
  if (!isMounted.value)
    return 'Account'

  const name = auth.user.value?.full_name || [auth.user.value?.first_name, auth.user.value?.last_name].filter(Boolean).join(' ')
  return name || auth.user.value?.email || 'Admin'
})
const notificationItems = computed(() => adminNotifications.notifications.value.slice(0, 8))
const unreadCount = computed(() => adminNotifications.unreadCount.value)
const pushConfig = computed(() => adminNotifications.pushConfig.value)
const pushError = computed(() => adminNotifications.pushError.value)
const canEnablePush = computed(() => Boolean(pushConfig.value?.is_configured && import.meta.client))
const pushButtonLabel = computed(() => {
  if (!pushConfig.value?.is_configured)
    return 'Push keys missing'
  if ((pushConfig.value?.active_subscription_count || 0) > 0)
    return 'Push enabled'
  return 'Enable push'
})

onMounted(() => {
  isMounted.value = true
  void adminNotifications.fetchNotifications()
  void adminNotifications.fetchPushConfig()
  notificationTimer = setInterval(() => {
    void adminNotifications.fetchNotifications()
  }, 45_000)
})

onBeforeUnmount(() => {
  if (notificationTimer)
    clearInterval(notificationTimer)
})

async function handleLogout() {
  await auth.logout()
}

function severityIcon(severity: string) {
  if (severity === 'success')
    return 'i-lucide-check-circle'
  if (severity === 'warning')
    return 'i-lucide-alert-triangle'
  if (severity === 'error' || severity === 'critical')
    return 'i-lucide-circle-alert'
  return 'i-lucide-info'
}

function severityClass(severity: string) {
  if (severity === 'success')
    return 'text-emerald-600 bg-emerald-50'
  if (severity === 'warning')
    return 'text-amber-600 bg-amber-50'
  if (severity === 'error' || severity === 'critical')
    return 'text-red-600 bg-red-50'
  return 'text-blue-700 bg-blue-50'
}

function formatNotificationTime(value: string) {
  if (!value)
    return ''
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

async function openNotification(notification: any) {
  if (!notification.read_at)
    await adminNotifications.markRead(notification.id)
  if (notification.action_url)
    await navigateTo(notification.action_url)
}

async function enablePush() {
  if ((pushConfig.value?.active_subscription_count || 0) > 0)
    return
  await adminNotifications.enableBrowserPush()
}
</script>

<template>
  <UApp
    :toaster="{
      position: 'bottom-right',
    }"
  >
    <NuxtPage v-if="isAuthPage" />

    <div v-else class="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <LayoutSidebar />

      <div class="min-h-screen lg:pl-64">
        <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
          <div class="flex h-18 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <NuxtLink to="/" class="flex items-center gap-3">
              <div class="flex h-11 w-14 items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-white">
                <img src="/brand/reesolmart-logo.jpg" alt="" class="h-full w-full object-contain">
              </div>
              <div>
                <p class="text-lg font-black leading-tight">
                  Reesolmart
                </p>
                <p class="text-xs text-slate-500 dark:text-slate-400">
                  Just in time, buying
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
              <UPopover>
                <UButton icon="i-lucide-bell" color="neutral" variant="ghost" class="relative" aria-label="Admin notifications">
                  <span
                    v-if="unreadCount"
                    class="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[11px] font-bold text-white"
                  >
                    {{ unreadCount > 9 ? '9+' : unreadCount }}
                  </span>
                </UButton>

                <template #content>
                  <div class="w-[min(92vw,390px)] p-3">
                    <div class="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
                      <div>
                        <p class="font-semibold text-slate-950 dark:text-white">
                          Admin notifications
                        </p>
                        <p class="text-xs text-slate-500">
                          {{ unreadCount }} unread operational alert{{ unreadCount === 1 ? '' : 's' }}
                        </p>
                      </div>
                      <UButton size="xs" color="neutral" variant="ghost" :disabled="!unreadCount" @click="adminNotifications.markAllRead">
                        Mark all read
                      </UButton>
                    </div>

                    <div class="mt-3 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-900">
                      <div class="min-w-0">
                        <p class="text-xs font-semibold uppercase text-slate-500">
                          Browser push
                        </p>
                        <p class="truncate text-sm text-slate-700 dark:text-slate-300">
                          {{ pushConfig?.is_configured ? 'Receive alerts when dashboard is closed.' : 'Configure VAPID keys on backend.' }}
                        </p>
                      </div>
                      <UButton size="xs" color="primary" variant="soft" :disabled="!canEnablePush || (pushConfig?.active_subscription_count || 0) > 0" @click="enablePush">
                        {{ pushButtonLabel }}
                      </UButton>
                    </div>
                    <p v-if="pushError" class="mt-2 text-xs text-red-600">
                      {{ pushError }}
                    </p>

                    <div class="mt-3 max-h-[420px] space-y-2 overflow-y-auto pr-1">
                      <button
                        v-for="notification in notificationItems"
                        :key="notification.id"
                        type="button"
                        class="flex w-full gap-3 rounded-lg border border-slate-200 p-3 text-left transition hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
                        :class="notification.read_at ? 'opacity-75' : 'bg-white dark:bg-slate-950'"
                        @click="openNotification(notification)"
                      >
                        <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full" :class="severityClass(notification.severity)">
                          <UIcon :name="severityIcon(notification.severity)" />
                        </span>
                        <span class="min-w-0 flex-1">
                          <span class="flex items-center gap-2">
                            <span class="truncate text-sm font-semibold text-slate-950 dark:text-white">{{ notification.title }}</span>
                            <span v-if="!notification.read_at" class="h-2 w-2 shrink-0 rounded-full bg-red-500" />
                          </span>
                          <span class="mt-1 line-clamp-2 text-sm text-slate-600 dark:text-slate-300">{{ notification.message }}</span>
                          <span class="mt-2 block text-xs text-slate-400">{{ formatNotificationTime(notification.created_at) }}</span>
                        </span>
                      </button>

                      <div v-if="!notificationItems.length" class="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                        No admin notifications yet.
                      </div>
                    </div>
                  </div>
                </template>
              </UPopover>
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
          <NuxtPage />
        </main>
      </div>
    </div>
  </UApp>
</template>
