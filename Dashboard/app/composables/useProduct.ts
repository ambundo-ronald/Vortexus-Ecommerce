import type { ProductImageItem } from '~/types/ProductImage'

export interface ProductListParams {
  page?: number
  pageSize?: number
  search?: string
  status?: 'active' | 'draft' | ''
  sortBy?: string
  sortDir?: 'asc' | 'desc'
}

export interface ProductOptionParams {
  excludeId?: number | string
  maxPages?: number
  pageSize?: number
  search?: string
}

const DEFAULT_CURRENCY = 'KES'

export const DOMAIN_PRODUCT_CLASS_OPTIONS = [
  { label: 'Standard catalogue product', value: '' },
  { label: 'Filter', value: 'filter' },
  { label: 'Blower', value: 'blower' },
  { label: 'Chemical', value: 'chemical' },
  { label: 'Controller', value: 'controller' },
  { label: 'Desalination system', value: 'desalination_system' },
  { label: 'Flow meter', value: 'flow_meter' },
  { label: 'Plumbing fitting', value: 'plumbing_fitting' },
  { label: 'Sterilizer', value: 'sterilizer' },
  { label: 'Surface pump', value: 'surface_pump' },
  { label: 'Submersible pump', value: 'submersible_pump' },
  { label: 'Vessel', value: 'vessel' },
]

function normalizeImageId(id: unknown): number | undefined {
  const value = Number(id)
  return Number.isInteger(value) && value > 0 ? value : undefined
}

function mapProductImage(image: any): ProductImageItem {
  return {
    ...image,
    id: normalizeImageId(image?.id),
    alt: image?.alt || '',
    src: mediaUrl(image?.src),
  }
}

function mapSort(sortBy?: string, sortDir: 'asc' | 'desc' = 'asc') {
  if (sortBy === 'price')
    return sortDir === 'desc' ? 'price_desc' : 'price_asc'
  if (sortBy === 'name')
    return 'title_asc'
  if (sortBy === 'id')
    return 'newest'
  return 'relevance'
}

function flattenCategories(results: any[] = []) {
  const flattened: { label: string, value: string }[] = []
  const byId = new Map(results.map(category => [category.id, category]))
  for (const category of results) {
    const parent = category.parent_id ? byId.get(category.parent_id) : null
    flattened.push({
      label: parent ? `${parent.name} / ${category.name}` : category.name,
      value: String(category.id),
    })
    for (const child of category.children || [])
      flattened.push({ label: `${category.name} / ${child.name}`, value: String(child.id) })
  }
  return flattened
}

function mapProductDetailToForm(product: any) {
  const firstCategoryId = product.categoryIds?.[0] ? String(product.categoryIds[0]) : ''
  const specificationMap = Object.fromEntries((product.specifications || []).map((item: any) => [item.code, item.value]))
  const domainProduct = product.domain_product || null
  const domainPayload = domainProduct?.payload && typeof domainProduct.payload === 'object'
    ? domainProduct.payload
    : null

  return {
    id: product.id,
    name: product.name,
    description: product.description || '',
    slug: product.slug || '',
    metaTitle: product.metaTitle || '',
    metaDescription: product.metaDescription || '',
    recommendedProductIds: (product.recommendedProductIds || []).map((id: any) => Number(id)),
    price: Number(product.price || 0),
    currency: product.currency || DEFAULT_CURRENCY,
    originalPrice: undefined,
    chargeTax: true,
    sku: product.sku || '',
    stock: Number(product.stock || 0),
    weight: product.weight ?? (specificationMap.weight_grams ? Number(specificationMap.weight_grams) : null),
    dimensions: product.dimensions || specificationMap.dimensions || '',
    status: product.status || (product.isPublic ? 'active' : 'draft'),
    category: firstCategoryId,
    brand: product.brand || specificationMap.brand || '',
    tags: product.tags || specificationMap.tags || '',
    attributes: specificationMap,
    productClass: domainProduct?.product_class || '',
    domainSpecsText: domainPayload ? JSON.stringify(domainPayload, null, 2) : '',
    images: (product.images || []).map((image: any) => mapProductImage(image)),
  }
}

function mapFormToPayload(data: Record<string, any>) {
  const dynamicAttributes = data.attributes && typeof data.attributes === 'object'
    ? data.attributes
    : {}
  const domainSpecsText = String(data.domainSpecsText || '').trim()
  const payload: Record<string, any> = {
    upc: data.sku,
    title: data.name,
    slug: data.slug || '',
    description: data.description || '',
    meta_title: data.metaTitle || '',
    meta_description: data.metaDescription || '',
    is_public: data.status === 'active',
    category_ids: data.category && data.category !== '__uncategorized__' ? [Number(data.category)] : [],
    recommended_product_ids: Array.isArray(data.recommendedProductIds) ? data.recommendedProductIds.map(Number) : [],
    price: Number(data.price || 0),
    currency: data.currency || DEFAULT_CURRENCY,
    num_in_stock: Number(data.stock || 0),
    attributes: {
      ...dynamicAttributes,
      weight_grams: data.weight ?? '',
      dimensions: data.dimensions || '',
      brand: data.brand || '',
      tags: data.tags || '',
    },
  }

  if (data.productClass)
    payload.product_class = data.productClass

  if (domainSpecsText)
    payload.domain_specs = JSON.parse(domainSpecsText)

  return payload
}

export function useProduct() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getProducts(params: ProductListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await request<{ results: any[], pagination: any }>('/admin/products/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 10,
          q: params.search || '',
          status: params.status || '',
          sort_by: mapSort(params.sortBy, params.sortDir || 'asc'),
        },
      })
      return {
        success: true,
        data: {
          ...response,
          results: (response.results || []).map(product => ({
            ...product,
            currency: product.currency || DEFAULT_CURRENCY,
            imageUrl: mediaUrl(product.imageUrl),
          })),
        },
      }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getProduct(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ product: any }>(`/admin/products/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: mapProductDetailToForm(result.product), raw: result.product }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getCategoryOptions() {
    try {
      const result = await request<{ results: any[] }>('/admin/catalog/categories/', {
        method: 'GET',
        query: {
          page: 1,
          page_size: 1000,
        },
      })
      return { success: true, data: flattenCategories(result.results || []) }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error', data: [] }
    }
  }

  async function getProductOptions(params: ProductOptionParams | number | string = {}) {
    try {
      const options = typeof params === 'object' && params !== null
        ? params
        : { excludeId: params }
      const pageSize = Math.min(options.pageSize || 60, 60)
      const maxPages = options.maxPages || 10
      const results: any[] = []
      let page = 1
      let hasNext = true

      while (hasNext && page <= maxPages) {
        const response = await request<{ results: any[], pagination?: { has_next?: boolean } }>('/admin/products/', {
          method: 'GET',
          query: {
            page,
            page_size: pageSize,
            q: options.search || '',
            sort_by: 'title_asc',
          },
        })
        results.push(...(response.results || []))
        hasNext = Boolean(response.pagination?.has_next)
        page += 1
      }

      const excluded = options.excludeId ? Number(options.excludeId) : null
      return {
        success: true,
        data: results
          .filter(product => Number(product.id) !== excluded)
          .map(product => ({
            label: `${product.name || product.title || `Product #${product.id}`}${product.sku ? ` (${product.sku})` : ''}`,
            value: String(product.id),
          })),
      }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error', data: [] }
    }
  }

  async function createProduct(data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ product: any }>('/admin/products/', {
        method: 'POST',
        body: mapFormToPayload(data),
      })
      return { success: true, data: result.product }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateProduct(id: number | string, data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ product: any }>(`/admin/products/${id}/`, {
        method: 'PATCH',
        body: mapFormToPayload(data),
      })
      return { success: true, data: result.product }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteProduct(id: number | string) {
    loading.value = true
    error.value = null
    try {
      await request(`/admin/products/${id}/`, {
        method: 'DELETE',
      })
      return { success: true }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function uploadProductImage(productId: number | string, image: ProductImageItem) {
    if (!image.file)
      return { success: true, data: image }

    const formData = new FormData()
    formData.append('image', image.file)
    formData.append('alt', image.alt || '')

    try {
      const result = await request<{ image: ProductImageItem }>(`/admin/products/${productId}/images/`, {
        method: 'POST',
        body: formData,
      })
      return { success: true, data: mapProductImage(result.image) }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  async function deleteProductImage(productId: number | string, imageId: number | string) {
    const normalizedImageId = normalizeImageId(imageId)
    if (!normalizedImageId)
      return { success: false, error: 'This image could not be removed because it is missing its saved image ID.' }

    try {
      await request(`/admin/products/${productId}/images/${normalizedImageId}/`, {
        method: 'DELETE',
      })
      return { success: true }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  async function syncProductImages(productId: number | string, nextImages: ProductImageItem[], previousImages: ProductImageItem[] = []) {
    const previousIds = new Set(previousImages.map(image => normalizeImageId(image.id)).filter((id): id is number => typeof id === 'number'))
    const nextIds = new Set(nextImages.map(image => normalizeImageId(image.id)).filter((id): id is number => typeof id === 'number'))

    const removedIds = [...previousIds].filter(id => !nextIds.has(id))
    for (const imageId of removedIds) {
      const deleteResult = await deleteProductImage(productId, imageId)
      if (!deleteResult.success)
        return deleteResult
    }

    const unsavedImages = nextImages.filter(image => image.file)
    const uploadedImages: ProductImageItem[] = []
    for (const image of unsavedImages) {
      const uploadResult = await uploadProductImage(productId, image)
      if (!uploadResult.success)
        return uploadResult
      uploadedImages.push(uploadResult.data as ProductImageItem)
    }

    const persistedImages = nextImages
      .filter(image => normalizeImageId(image.id) && !image.file)
      .map(image => ({ ...image, id: normalizeImageId(image.id) }))
      .concat(uploadedImages)

    return { success: true, data: persistedImages }
  }

  return {
    loading,
    error,
    createProduct,
    deleteProduct,
    deleteProductImage,
    getProduct,
    getProductOptions,
    getProducts,
    getCategoryOptions,
    syncProductImages,
    uploadProductImage,
    updateProduct,
  }
}
