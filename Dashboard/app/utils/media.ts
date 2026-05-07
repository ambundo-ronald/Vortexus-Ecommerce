export function mediaUrl(src?: string | null) {
  if (!src)
    return ''

  if (src.startsWith('blob:') || src.startsWith('data:') || /^https?:\/\//.test(src))
    return src

  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase || '').replace(/\/api\/v1\/?$/, '')
  const origin = apiBase.replace(/\/$/, '')

  if (!origin)
    return src

  return `${origin}${src.startsWith('/') ? src : `/${src}`}`
}

export function formatMoney(value: number | string | null | undefined, currency = 'KES') {
  const amount = Number(value || 0)
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: currency || 'KES',
    maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
  }).format(amount)
}
