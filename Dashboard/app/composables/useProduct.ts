import { products } from '~/data/products'
export function useProduct() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function getProduct(id: number) {
    loading.value = true
    error.value = null
    try {
      // const result = await $fetch(`/api/products/${id}`)
      // return { success: true, data: result }
      const product = products.find((p: { id: number }) => p.id === parseInt(id))
      if (!product) throw new Error('Product not found')
      return { success: true, data: product }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function createProduct(data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      // const result = await $fetch('/api/products', {
      //   method: 'POST',
      //   body: data,
      // })
      // return { success: true, data: result }
      // For now, just return a fake product
      const fakeProduct = {
        id: 101,
        name: "Apple Watch Series 10",
        sku: "AW-S10-GPS",
        category: "Electronics",
        price: 499.0,
        stock: 10,
        status: "in-stock",
        imageUrl: "/images/products/watch10.png",
      }
      return { success: true, data: fakeProduct }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    createProduct,
    getProduct,
  }
}
