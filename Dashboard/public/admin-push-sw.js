self.addEventListener('push', (event) => {
  let payload = {}
  try {
    payload = event.data ? event.data.json() : {}
  }
  catch {
    payload = {}
  }

  const title = payload.title || 'Reesolmart admin'
  const options = {
    body: payload.body || 'New dashboard notification',
    icon: payload.icon || '/brand/reesolmart-logo.jpg',
    badge: payload.badge || '/brand/reesolmart-logo.jpg',
    data: {
      url: payload.url || '/',
      notificationId: payload.notification_id,
      eventType: payload.event_type,
    },
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const targetUrl = new URL(event.notification.data?.url || '/', self.location.origin).href

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          client.navigate(targetUrl)
          return client.focus()
        }
      }
      if (self.clients.openWindow)
        return self.clients.openWindow(targetUrl)
      return undefined
    }),
  )
})
