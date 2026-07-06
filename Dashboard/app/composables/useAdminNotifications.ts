export interface AdminNotification {
  id: number
  event_type: string
  event_key: string
  title: string
  message: string
  severity: 'info' | 'success' | 'warning' | 'error' | 'critical'
  action_url: string
  related_object_type: string
  related_object_id: string
  metadata: Record<string, any>
  read_at: string | null
  created_at: string
  updated_at: string
}

export interface AdminPushConfig {
  is_configured: boolean
  public_key: string
  active_subscription_count: number
}

function readApiError(err: any) {
  return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
}

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = `${base64String}${padding}`.replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; i += 1)
    outputArray[i] = rawData.charCodeAt(i)
  return outputArray
}

function detectBrowser() {
  if (!import.meta.client)
    return ''
  const userAgent = navigator.userAgent
  if (userAgent.includes('Edg/'))
    return 'Edge'
  if (userAgent.includes('Chrome/'))
    return 'Chrome'
  if (userAgent.includes('Firefox/'))
    return 'Firefox'
  if (userAgent.includes('Safari/'))
    return 'Safari'
  return 'Browser'
}

export function useAdminNotifications() {
  const notifications = useState<AdminNotification[]>('admin-notifications', () => [])
  const unreadCount = useState<number>('admin-notification-unread-count', () => 0)
  const pushConfig = useState<AdminPushConfig | null>('admin-push-config', () => null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pushError = ref<string | null>(null)
  const { request } = useBackendApi()

  async function fetchNotifications(options: { unread?: boolean, limit?: number } = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: AdminNotification[], unread_count: number }>('/admin/notifications/', {
        query: {
          unread: options.unread ? '1' : '',
          limit: options.limit || 20,
        },
      })
      notifications.value = result.results || []
      unreadCount.value = result.unread_count || 0
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function markRead(notificationId: number) {
    try {
      const result = await request<{ notification: AdminNotification }>(`/admin/notifications/${notificationId}/`, {
        method: 'PATCH',
        body: { action: 'read' },
      })
      notifications.value = notifications.value.map(item => item.id === notificationId ? result.notification : item)
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      return { success: true, data: result.notification }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
  }

  async function markAllRead() {
    try {
      const result = await request<{ updated: number }>('/admin/notifications/read-all/', { method: 'POST' })
      notifications.value = notifications.value.map(item => ({ ...item, read_at: item.read_at || new Date().toISOString() }))
      unreadCount.value = 0
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
  }

  async function fetchPushConfig() {
    pushError.value = null
    try {
      const result = await request<AdminPushConfig>('/admin/push/config/')
      pushConfig.value = result
      return { success: true, data: result }
    }
    catch (err: any) {
      pushError.value = readApiError(err)
      return { success: false, error: pushError.value }
    }
  }

  async function enableBrowserPush() {
    pushError.value = null
    if (!import.meta.client)
      return { success: false, error: 'Browser push can only be enabled in the browser.' }
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
      pushError.value = 'This browser does not support web push notifications.'
      return { success: false, error: pushError.value }
    }
    const config = pushConfig.value || (await fetchPushConfig()).data
    if (!config?.is_configured || !config.public_key) {
      pushError.value = 'Web Push VAPID keys are not configured on the backend.'
      return { success: false, error: pushError.value }
    }
    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
      pushError.value = 'Notification permission was not granted.'
      return { success: false, error: pushError.value }
    }
    const registration = await navigator.serviceWorker.register('/admin-push-sw.js')
    const existing = await registration.pushManager.getSubscription()
    const subscription = existing || await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(config.public_key),
    })
    const body = subscription.toJSON()
    const result = await request('/admin/push/subscription/', {
      method: 'POST',
      body: {
        subscription: {
          endpoint: body.endpoint,
          keys: body.keys,
          browser: detectBrowser(),
        },
      },
    })
    await fetchPushConfig()
    return { success: true, data: result }
  }

  return {
    notifications,
    unreadCount,
    pushConfig,
    loading,
    error,
    pushError,
    fetchNotifications,
    markRead,
    markAllRead,
    fetchPushConfig,
    enableBrowserPush,
  }
}
