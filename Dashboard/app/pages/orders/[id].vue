<script setup lang="ts">
const route = useRoute();
const { getOrder, updateOrderStatus } = useOrder();
const toast = useToast();

const order = ref<any>(null);
const isLoading = ref(true);
const isSaving = ref(false);
const statusForm = reactive({
  status: "",
  tracking_reference: "",
  note: "",
});
const statusOptions = computed(() =>
  (order.value?.availableStatuses || []).map((status: string) => ({
    label: status,
    value: status,
  }))
);

const orderSteps = computed(() => {
  if (!order.value)
    return [];

  const tracking = order.value.tracking || [];
  const statuses = tracking.map((item: any) => String(item.status || "").toLowerCase());

  const isPacked = statuses.some((status: string) => status.includes("pack"));
  const isShipped = statuses.some((status: string) => status.includes("ship"));
  const isDelivered = statuses.some((status: string) => status.includes("deliver") || status.includes("success"));

  return [
    { label: "Placed", status: "completed" },
    { label: "Packed", status: isPacked ? "completed" : "current" },
    { label: "Shipped", status: isShipped ? "completed" : "future" },
    { label: "Delivered", status: isDelivered ? "completed" : "future" },
  ];
});

const googleMapsUrl = computed(() => {
  const shippingAddress = order.value?.shippingAddress;
  if (!shippingAddress)
    return "";
  const address = encodeURIComponent([
    shippingAddress.street,
    shippingAddress.city,
    shippingAddress.state,
    shippingAddress.zipCode,
  ].filter(Boolean).join(", "));
  return `https://www.google.com/maps?q=${address}&output=embed`;
});

const formatDate = (dateString: string) =>
  new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

const formatTime = (dateString: string) =>
  new Date(dateString).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

function discardChanges() {
  navigateTo("/orders");
}

async function loadOrder() {
  const result = await getOrder(route.params.id as string);
  if (result.success) {
    order.value = result.data;
    statusForm.status = result.data?.status || "";
    statusForm.tracking_reference = result.data?.trackingReference || "";
    statusForm.note = "";
  }
  else {
    toast.add({
      title: "Could not load order",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
}

async function submitStatusUpdate() {
  if (!order.value || !statusForm.status)
    return;

  isSaving.value = true;
  const result = await updateOrderStatus(order.value.id, {
    status: statusForm.status,
    tracking_reference: statusForm.tracking_reference,
    note: statusForm.note,
  });

  if (result.success) {
    order.value = result.data;
    statusForm.status = result.data?.status || statusForm.status;
    statusForm.tracking_reference = result.data?.trackingReference || statusForm.tracking_reference;
    statusForm.note = "";
    toast.add({
      title: "Order updated",
      description: result.detail || "Order status updated successfully.",
      color: "success",
    });
  }
  else {
    toast.add({
      title: "Update failed",
      description: result.error || "Could not update order.",
      color: "error",
    });
  }

  isSaving.value = false;
}

onMounted(async () => {
  await loadOrder();
  isLoading.value = false;
});
</script>

<template>
  <div>
    <div v-if="isLoading" class="flex min-h-96 items-center justify-center">
      <UIcon
        name="i-lucide-loader-2"
        class="h-8 w-8 animate-spin text-toned dark:text-muted"
      />
    </div>

    <div v-else-if="order" class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between pb-6">
        <div class="flex items-center gap-4">
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            size="md"
            square
            aria-label="Back to orders"
            @click="discardChanges"
          />
          <h1 class="truncate text-xl font-semibold text-default">
            {{ order.orderNo }}
          </h1>
        </div>
      </div>

      <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-3">
        <div class="space-y-6 lg:col-span-2">
          <Stepper :steps="orderSteps" />

          <UCard>
            <template #header>
              <h3 class="text-lg font-bold text-default">Order Details</h3>
            </template>

            <div class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <div class="mb-1 text-sm text-toned dark:text-muted">
                    Created
                  </div>
                  <div class="font-medium tracking-tight text-default">
                    {{ formatDate(order.createdDate) }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-toned dark:text-muted">Total</div>
                  <div class="font-medium tracking-tight text-default">
                    ${{ order.orderTotal.toFixed(2) }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-toned dark:text-muted">
                    Order Via
                  </div>
                  <div class="font-medium tracking-tight text-default">
                    {{ order.orderVia }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-toned dark:text-muted">
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
                <h4 class="mb-3 text-base font-semibold text-default">
                  <UIcon
                    name="i-lucide-map-pin"
                    class="mr-2 inline h-4 w-4 text-primary"
                  />
                  Shipping Information
                </h4>
                <div class="space-y-4 rounded-lg bg-elevated p-4">
                  <div class="font-medium tracking-tight text-default">
                    {{ order.shippingAddress?.street || "No shipping address provided" }}<br>
                    <template v-if="order.shippingAddress">
                      {{ order.shippingAddress.city }},
                      {{ order.shippingAddress.state }}
                      {{ order.shippingAddress.zipCode }}
                    </template>
                  </div>
                  <iframe
                    v-if="order.shippingAddress"
                    class="h-56 w-full rounded-lg border border-muted"
                    style="min-height:224px"
                    :src="googleMapsUrl"
                    allowfullscreen
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"
                  />
                </div>
              </div>

              <div>
                <h4 class="mb-3 text-base font-semibold text-default">
                  Products
                </h4>
                <div class="space-y-4">
                  <div
                    v-for="product in order.products"
                    :key="product.id"
                    class="flex items-center gap-4 rounded-lg bg-elevated p-4"
                  >
                    <img
                      :src="product.image || 'https://placehold.co/400x400/64748b/ffffff?text=N/A'"
                      :alt="product.name"
                      class="h-12 w-12 rounded-lg object-cover"
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
                      ${{ Number(product.price || 0).toFixed(2) }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="border-t border-muted pt-4">
                <div class="space-y-2">
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Subtotal</span>
                    <span class="text-default">${{ Number(order.subtotal || 0).toFixed(2) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Shipping</span>
                    <span class="text-default">${{ Number(order.shipping || 0).toFixed(2) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-toned dark:text-muted">Tax</span>
                    <span class="text-default">${{ Number(order.tax || 0).toFixed(2) }}</span>
                  </div>
                  <div class="flex justify-between border-t border-muted pt-2 text-lg font-semibold text-default">
                    <span>Total</span>
                    <span>${{ order.orderTotal.toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </UCard>
        </div>

        <div class="space-y-6">
          <UCard>
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-settings-2" class="h-5 w-5 text-default" />
                <h3 class="text-lg font-bold text-default">Admin Actions</h3>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-default">Order status</label>
                  <USelect
                    v-model="statusForm.status"
                    :items="statusOptions"
                    value-attribute="value"
                    option-attribute="label"
                    size="lg"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-default">Tracking reference</label>
                  <UInput
                    v-model="statusForm.tracking_reference"
                    size="lg"
                    placeholder="TRK-1001"
                  />
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-default">Internal note</label>
                <UTextarea
                  v-model="statusForm.note"
                  :rows="4"
                  placeholder="Add an update note for this order..."
                />
              </div>

              <div class="flex items-center justify-end gap-3">
                <UButton
                  color="neutral"
                  variant="outline"
                  :disabled="isSaving"
                  @click="loadOrder"
                >
                  Refresh order
                </UButton>
                <UButton
                  color="primary"
                  variant="solid"
                  :loading="isSaving"
                  @click="submitStatusUpdate"
                >
                  Save update
                </UButton>
              </div>
            </div>
          </UCard>

          <UCard>
            <template #header>
              <h3 class="text-lg font-bold text-default">Customer</h3>
            </template>

            <div class="space-y-6">
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10"
                  >
                    <UIcon name="i-lucide-user" class="h-6 w-6 text-primary" />
                  </div>
                  <div
                    class="absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-bg bg-success"
                  />
                </div>
                <div>
                  <div class="font-medium text-default">
                    {{ order.customer?.name || order.companyName }}
                  </div>
                  <div class="text-sm text-toned dark:text-muted">
                    {{ order.customer?.company || order.companyName }}
                  </div>
                </div>
              </div>

              <div class="space-y-3">
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-mail" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Email</div>
                    <div class="font-medium tracking-tight text-default">
                      {{ order.customer?.email || "No email available" }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-phone" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Phone</div>
                    <div class="font-medium tracking-tight text-default">
                      {{ order.customer?.phone || "No phone available" }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-building" class="h-4 w-4 text-toned dark:text-muted" />
                  <div>
                    <div class="text-sm text-toned dark:text-muted">Company</div>
                    <div class="font-medium tracking-tight text-default">
                      {{ order.customer?.company || order.companyName }}
                    </div>
                  </div>
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
                    <span class="font-medium text-danger">{{ order.status }}</span>
                  </div>
                </div>
              </div>
            </template>

            <div class="relative pl-8">
              <div
                class="absolute bottom-0 left-3 top-0 w-px border-l-2 border-dashed border-muted"
              />

              <div class="space-y-6">
                <div v-for="(item, index) in order.tracking" :key="index" class="relative">
                  <div
                    class="absolute -left-[1.375rem] top-1 h-3 w-3 rounded-full"
                    :class="{
                      'bg-warning': item.status !== 'Success' && item.status !== 'Delivered',
                      'bg-success': item.status === 'Success' || item.status === 'Delivered',
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

          <UCard v-if="order.supplierGroups?.length">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-boxes" class="h-5 w-5 text-default" />
                <h3 class="text-lg font-bold text-default">Supplier Groups</h3>
              </div>
            </template>

            <div class="space-y-4">
              <div
                v-for="group in order.supplierGroups"
                :key="group.id"
                class="rounded-lg border border-muted p-4"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <div>
                    <div class="font-medium text-default">{{ group.name }}</div>
                    <div class="text-sm text-toned dark:text-muted">
                      {{ group.itemCount }} items across {{ group.lineCount }} lines
                    </div>
                  </div>
                  <UBadge
                    :label="group.status"
                    color="neutral"
                    variant="soft"
                    class="capitalize"
                  />
                </div>
                <div class="space-y-1 text-sm text-toned dark:text-muted">
                  <div v-if="group.trackingReference">
                    Tracking: <span class="font-medium text-default">{{ group.trackingReference }}</span>
                  </div>
                  <div v-if="group.notes">
                    Note: <span class="font-medium text-default">{{ group.notes }}</span>
                  </div>
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </div>

    <div v-else class="flex min-h-96 items-center justify-center">
      <div class="text-center">
        <UIcon
          name="i-lucide-package-x"
          class="mx-auto mb-4 h-12 w-12 text-toned dark:text-muted"
        />
        <p class="text-default">Order not found</p>
      </div>
    </div>
  </div>
</template>
