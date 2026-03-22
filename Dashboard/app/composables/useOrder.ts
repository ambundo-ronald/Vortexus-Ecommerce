import { orders } from '~/data/orderData'
export function useOrder() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function getOrder(id: number) {
    loading.value = true
    error.value = null
    try {
      // const result = await $fetch(`/api/orders/${id}`)
      // return { success: true, data: result }
      const order = orders.find((o: { id: number }) => o.id === Number(id))
      if (!order) throw new Error('Order not found')
      return { success: true, data: order }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function createOrder(data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      // const result = await $fetch('/api/orders', {
      //   method: 'POST',
      //   body: data,
      // })
      // return { success: true, data: result }
      // For now, just return a fake order
      const fakeOrder = {
        id: 101,
        userId: 1,
        status: "pending",
        total: 199.99,
        createdAt: new Date().toISOString(),
        items: [
          {
            productId: 1,
            name: "Sample Product",
            quantity: 2,
            price: 99.99,
          },
        ],
      }
      return { success: true, data: fakeOrder }
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
    createOrder,
    getOrder
  }
}
