<script setup lang="ts">
const route = useRoute();

const { data: order, status } = await useFetch(`/api/orders/${route.params.id}`);

const orderSteps = computed(() => {
  if (!order) return [];

  return [
    {
      label: "Quoted",
      status: "completed",
    },
    {
      label: "Packed",
      status: "completed",
    },
    {
      label: "Shipped",
      status: order.fulfilled ? "future" : "future",
    },
    {
      label: "Delivered",
      status: order.paid ? "future" : "future",
    },
  ];
});

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const googleMapsUrl = computed(() => {
  if (!order?.shippingAddress) return "";
  const { street, city, state, zipCode } = order.shippingAddress;
  const address = encodeURIComponent(`${street}, ${city}, ${state} ${zipCode}`);
  return `https://www.google.com/maps?q=${address}&output=embed&hl=en&pb=!1m18!1m12!1m3!1d0!2d0!3d0!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0:0x0!2z!5e0!3m2!1sen!2sus!4v0!5m2!1sen!2sus&controls=0&disableDefaultUI=1&zoomControl=0&mapTypeControl=0&streetViewControl=0&fullscreenControl=0`;
});

function discardChanges() {
  navigateTo("/orders");
}
</script>

<template>
  <div>
    <div v-if="status === 'pending'" class="flex items-center justify-center min-h-96">
      <UIcon
        name="i-lucide-loader-2"
        class="animate-spin h-8 w-8 text-toned dark:text-muted"
      />
    </div>

    <div v-if="order" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex justify-between items-center pb-6">
        <div class="flex items-center gap-4">
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            size="md"
            square
            aria-label="Back to products"
            @click="discardChanges"
          />
          <h1 class="text-xl font-semibold text-default truncate">
            {{ order.orderNo }}
          </h1>
        </div>
        <div class="flex items-center gap-3">
          <UButton
            label="Discard"
            color="neutral"
            variant="outline"
            @click="discardChanges"
          />
          <UButton type="submit" color="primary" variant="solid">
            Save
            <UIcon name="i-lucide-save" class="ml-2" />
          </UButton>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div class="lg:col-span-2 space-y-6">
          <Stepper :steps="orderSteps" />

          <UCard>
            <template #header>
              <h3 class="text-lg font-bold text-default">Order Details</h3>
            </template>

            <div class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <div class="text-sm text-toned dark:text-muted mb-1">
                    Created
                  </div>
                  <div class="text-default font-medium tracking-tight">
                    {{ formatDate(order.createdDate) }}
                  </div>
                </div>
                <div>
                  <div class="text-sm text-toned dark:text-muted mb-1">Total</div>
                  <div class="text-default font-medium tracking-tight">
                    ${{ order.orderTotal.toFixed(2) }}
                  </div>
                </div>
                <div>
                  <div class="text-sm text-toned dark:text-muted mb-1">
                    Order Via
                  </div>
                  <div class="text-default font-medium tracking-tight">{{ order.orderVia }}</div>
                </div>
                <div>
                  <div class="text-sm text-toned dark:text-muted mb-1">
                    Order Stage
                  </div>
                  <UBadge
                    color="success"
                    variant="soft"
                    size="lg"
                    class="capitalize"
                  >
                    {{ order.status }}
                  </UBadge>
                </div>
              </div>

              <div>
                <h4 class="text-base font-semibold text-default mb-3">
                  <UIcon
                    name="i-lucide-map-pin"
                    class="h-4 w-4 inline mr-2 text-primary"
                  />
                  Shipping Information
                </h4>
                <div class="p-4 rounded-lg bg-elevated space-y-4">
                  <div class="text-default font-medium tracking-tight">
                    {{ order.shippingAddress?.street }}<br />
                    {{ order.shippingAddress?.city }},
                    {{ order.shippingAddress?.state }}
                    {{ order.shippingAddress?.zipCode }}
                  </div>
                    <iframe
                    v-if="order.shippingAddress"
                    class="w-full h-56 rounded-lg border border-muted"
                    style="min-height:224px"
                    :src="googleMapsUrl"
                    allowfullscreen
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"
                    />
                </div>
              </div>

              <div>
                <h4 class="text-base font-semibold text-default mb-3">
                  Products
                </h4>
                <div class="space-y-4">
                  <div
                    v-for="product in order.products"
                    :key="product.id"
                    class="flex items-center gap-4 p-4 rounded-lg bg-elevated"
                  >
                    <img
                      :src="product.image"
                      :alt="product.name"
                      class="w-12 h-12 rounded-lg object-cover"
                    >
                    <div class="flex-1">
                      <div class="font-medium text-default">
                        {{ product.name }}
                      </div>
                      <div class="text-sm text-toned dark:text-muted">
                        Qty: {{ product.quantity }}
                      </div>
                    </div>
                    <div class="font-semibold text-default">
                      ${{ product.price?.toFixed(2) }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="pt-4 border-t border-muted">
                <div class="space-y-2">
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Subtotal</span>
                    <span class="text-default"
                      >${{ order.subtotal?.toFixed(2) }}</span
                    >
                  </div>
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Shipping</span>
                    <span class="text-default"
                      >${{ order.shipping?.toFixed(2) }}</span
                    >
                  </div>
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Tax</span>
                    <span class="text-default"
                      >${{ order.tax?.toFixed(2) }}</span
                    >
                  </div>
                  <div
                    class="flex justify-between text-lg font-semibold text-default pt-2 border-t border-muted"
                  >
                    <span>Total</span>
                    <span
                      >${{ order.orderTotal.toFixed(2) }}</span
                    >
                  </div>
                </div>
              </div>

              <div class="flex justify-end gap-3 pt-4">
                <UButton variant="outline" color="neutral"> Cancel </UButton>
                <UButton color="primary" variant="solid"> Edit Order </UButton>
              </div>
            </div>
          </UCard>
        </div>

        <div class="space-y-6">
          <UCard>
            <template #header>
                <h3 class="text-lg font-bold text-default">Customer</h3>
            </template>

            <div class="space-y-6">
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div
                    class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center"
                  >
                    <UIcon name="i-lucide-user" class="h-6 w-6 text-primary" />
                  </div>
                  <div
                    class="absolute -bottom-1 -right-1 w-4 h-4 bg-success rounded-full border-2 border-bg"
                  />
                </div>
                <div>
                  <div class="font-medium text-default">
                    {{ order.companyName }}
                  </div>
                  <div class="text-sm text-toned dark:text-muted">Premium Customer</div>
                </div>
              </div>

              <div class="space-y-3">
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-mail" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Email</div>
                    <div class="text-default font-medium tracking-tight">
                      contact@{{
                        order.companyName.toLowerCase().replace(/\s+/g, "")
                      }}.com
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-phone" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Phone</div>
                    <div class="text-default font-medium tracking-tight">+1 (555) 123-4567</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-building" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Company</div>
                    <div class="text-default font-medium tracking-tight">{{ order.companyName }}</div>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4 pt-4 border-t border-muted">
                <div class="text-center">
                  <div class="text-lg font-semibold text-default">12</div>
                  <div class="text-sm text-toned dark:text-muted">Total Orders</div>
                </div>
                <div class="text-center">
                  <div class="text-lg font-semibold text-default">Total Spent</div>
                  <div class="text-sm text-toned dark:text-muted">$2,450</div>
                </div>
              </div>
            </div>
          </UCard>

          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-truck" class="h-5 w-5 text-default" />
                  <h3 class="text-lg font-bold text-default">Tracking</h3>
                </div>
                <div class="flex flex-col items-end gap-1">
                  <div class="text-sm text-toned dark:text-muted">
                    <span>Status : </span>
                    <span class="text-danger font-medium">In Transit</span>
                  </div>
                </div>
              </div>
            </template>

            <div class="relative pl-8">
              <div
                class="absolute left-3 top-0 bottom-0 w-px border-l-2 border-dashed border-muted"
              />

              <div class="space-y-6">
                <div v-for="(item, index) in order.tracking" :key="index" class="relative">
                  <div
                    class="absolute -left-[1.375rem] top-1 w-3 h-3 rounded-full"
                    :class="{
                      'bg-warning': item.status !== 'Success' && item.status !== 'Destination Warehouse',
                      'border-2 border-danger bg-bg': item.status === 'Destination Warehouse',
                      'bg-success': item.status === 'Success',
                    }"
                  />
                  <div class="space-y-1">
                    <div class="font-medium text-default">
                      {{ item.status }} ({{ formatTime(item.date) }})
                    </div>
                    <div class="text-sm text-toned dark:text-muted">
                      {{ item.location }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </div>

    <div v-else class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <UIcon
          name="i-lucide-package-x"
          class="h-12 w-12 mx-auto mb-4 text-toned dark:text-muted"
        />
        <p class="text-default">Order not found</p>
      </div>
    </div>
  </div>
</template>