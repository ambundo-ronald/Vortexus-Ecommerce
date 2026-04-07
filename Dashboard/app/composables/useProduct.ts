import type { ProductImageItem } from '~/types/ProductImage'

export interface ProductListParams {
  page?: number
  pageSize?: number
  search?: string
  sortBy?: string
  sortDir?: 'asc' | 'desc'
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
  for (const category of results) {
    flattened.push({ label: category.name, value: String(category.id) })
    for (const child of category.children || [])
      flattened.push({ label: `${category.name} / ${child.name}`, value: String(child.id) })
  }
  return flattened
}

function mapProductDetailToForm(product: any) {
  const firstCategoryId = product.categoryIds?.[0] ? String(product.categoryIds[0]) : ''
  const specificationMap = Object.fromEntries((product.specifications || []).map((item: any) => [item.code, item.value]))

  return {
    id: product.id,
    name: product.name,
    description: product.description || '',
    price: Number(product.price || 0),
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
    images: product.images || [],
  }
}

function mapFormToPayload(data: Record<string, any>) {
  return {
    upc: data.sku,
    title: data.name,
    description: data.description || '',
    is_public: data.status === 'active',
    category_ids: data.category ? [Number(data.category)] : [],
    price: Number(data.price || 0),
    currency: 'USD',
    num_in_stock: Number(data.stock || 0),
    attributes: {
      weight_grams: data.weight ?? '',
      dimensions: data.dimensions || '',
      brand: data.brand || '',
      tags: data.tags || '',
    },
  }
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
          sort_by: mapSort(params.sortBy, params.sortDir || 'asc'),
        },
      })
      return { success: true, data: response }
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
      const result = await request<{ results: any[] }>('/catalog/categories/', { method: 'GET' })
      return { success: true, data: flattenCategories(result.results || []) }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error', data: [] }
    }
  }

  async function createProduct(data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ product: any }>('/catalog/products/', {
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
      const result = await request<{ product: any }>(`/catalog/products/${id}/`, {
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
      await request(`/catalog/products/${id}/`, {
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
      return { success: true, data: result.image }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  async function deleteProductImage(productId: number | string, imageId: number) {
    try {
      await request(`/admin/products/${productId}/images/${imageId}/`, {
        method: 'DELETE',
      })
      return { success: true }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  async function syncProductImages(productId: number | string, nextImages: ProductImageItem[], previousImages: ProductImageItem[] = []) {
    const previousIds = new Set(previousImages.map(image => image.id).filter((id): id is number => typeof id === 'number'))
    const nextIds = new Set(nextImages.map(image => image.id).filter((id): id is number => typeof id === 'number'))

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
      .filter(image => typeof image.id === 'number' && !image.file)
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
    getProducts,
    getCategoryOptions,
    syncProductImages,
    uploadProductImage,
    updateProduct,
  }
}
