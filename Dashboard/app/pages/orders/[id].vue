<script setup lang="ts">
const route = useRoute();
const { addOrderNote, getOrder, getOrderLine, getOrderNotes, updateOrderShippingAddress, updateOrderStatus } = useOrder();
const toast = useToast();

const order = ref<any>(null);
const selectedLine = ref<any>(null);
const isLoading = ref(true);
const isSaving = ref(false);
const isSavingAddress = ref(false);
const isSavingNote = ref(false);
const isEditingAddress = ref(false);
const isLineDetailOpen = ref(false);
const isLoadingLine = ref(false);
const statusForm = reactive({
  status: "",
  tracking_reference: "",
  note: "",
});
const shippingForm = reactive({
  first_name: "",
  last_name: "",
  line1: "",
  line2: "",
  line3: "",
  line4: "",
  state: "",
  postcode: "",
  country_code: "KE",
  phone_number: "",
  notes: "",
  latitude: "",
  longitude: "",
  location_label: "",
});
const noteForm = reactive({
  note_type: "Admin",
  message: "",
});
const statusOptions = computed(() =>
  (order.value?.availableStatuses || []).map((status: string) => ({
    label: status,
    value: status,
  }))
);

function statusColor(status: string) {
  const normalized = String(status || "").toLowerCase();

  if (["paid", "delivered", "complete", "completed", "success"].includes(normalized))
    return "success";
  if (["packed", "shipped", "processing"].includes(normalized))
    return "primary";
  if (["failed", "cancelled", "canceled"].includes(normalized))
    return "error";
  if (["pending"].includes(normalized))
    return "warning";

  return "neutral";
}

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
  const location = shippingAddress.location;
  if (location?.latitude && location?.longitude)
    return `https://www.google.com/maps?q=${encodeURIComponent(`${location.latitude},${location.longitude}`)}&output=embed`;
  const address = encodeURIComponent([
    shippingAddress.street,
    shippingAddress.city,
    shippingAddress.state,
    shippingAddress.zipCode,
  ].filter(Boolean).join(", "));
  return `https://www.google.com/maps?q=${address}&output=embed`;
});

const googleMapsLink = computed(() => {
  const shippingAddress = order.value?.shippingAddress;
  if (!shippingAddress)
    return "";
  const location = shippingAddress.location;
  if (location?.latitude && location?.longitude)
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${location.latitude},${location.longitude}`)}`;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent([
    shippingAddress.street,
    shippingAddress.city,
    shippingAddress.state,
    shippingAddress.zipCode,
  ].filter(Boolean).join(", "))}`;
});

const formatDate = (dateString: string) =>
  dateString ? new Date(dateString).toLocaleDateString("en-KE", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }) : "Not available";

const formatTime = (dateString: string) =>
  dateString ? new Date(dateString).toLocaleTimeString("en-KE", {
    hour: "2-digit",
    minute: "2-digit",
  }) : "";

const formatDateTime = (dateString: string) =>
  dateString ? new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateString)) : "Not available";

function discardChanges() {
  navigateTo("/orders");
}

function fillShippingForm(address: any = {}) {
  shippingForm.first_name = address?.firstName || address?.first_name || "";
  shippingForm.last_name = address?.lastName || address?.last_name || "";
  shippingForm.line1 = address?.line1 || address?.street || "";
  shippingForm.line2 = address?.line2 || "";
  shippingForm.line3 = address?.line3 || "";
  shippingForm.line4 = address?.line4 || address?.city || "";
  shippingForm.state = address?.state || "";
  shippingForm.postcode = address?.postcode || address?.zipCode || "";
  shippingForm.country_code = address?.countryCode || address?.country_code || "KE";
  shippingForm.phone_number = address?.phoneNumber || address?.phone_number || "";
  shippingForm.notes = address?.notes || "";
  shippingForm.latitude = address?.location?.latitude != null ? String(address.location.latitude) : "";
  shippingForm.longitude = address?.location?.longitude != null ? String(address.location.longitude) : "";
  shippingForm.location_label = address?.location?.label || "";
}

async function loadOrder() {
  const result = await getOrder(route.params.id as string);
  if (result.success) {
    order.value = result.data;
    statusForm.status = result.data?.status || "";
    statusForm.tracking_reference = result.data?.trackingReference || "";
    statusForm.note = "";
    fillShippingForm(result.data?.shippingAddress || {});
  }
  else {
    toast.add({
      title: "Could not load order",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
}

async function refreshOrderNotes() {
  if (!order.value?.orderNo)
    return;

  const result = await getOrderNotes(order.value.orderNo);
  if (result.success)
    order.value.notes = result.data || [];
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

async function submitShippingAddress() {
  if (!order.value?.orderNo)
    return;
  if (!shippingForm.first_name.trim() || !shippingForm.last_name.trim() || !shippingForm.line1.trim() || !shippingForm.line4.trim()) {
    toast.add({
      title: "Address incomplete",
      description: "First name, last name, address line 1, and city are required.",
      color: "warning",
    });
    return;
  }

  isSavingAddress.value = true;
  const payload = {
    first_name: shippingForm.first_name.trim(),
    last_name: shippingForm.last_name.trim(),
    line1: shippingForm.line1.trim(),
    line2: shippingForm.line2.trim(),
    line3: shippingForm.line3.trim(),
    line4: shippingForm.line4.trim(),
    state: shippingForm.state.trim(),
    postcode: shippingForm.postcode.trim(),
    country_code: shippingForm.country_code.trim().toUpperCase(),
    phone_number: shippingForm.phone_number.trim(),
    notes: shippingForm.notes.trim(),
    latitude: shippingForm.latitude.trim() || null,
    longitude: shippingForm.longitude.trim() || null,
    location_label: shippingForm.location_label.trim(),
  };
  let result = await updateOrderShippingAddress(order.value.orderNo, payload);

  if (!result.success && (result as any).code === "delivery_change_requires_confirmation") {
    const changedFields = Array.isArray((result as any).errors?.changed_fields) ? (result as any).errors.changed_fields.join(", ") : "delivery details";
    const confirmed = window.confirm(`This order is already paid or in fulfillment. Confirm changing ${changedFields}?`);
    if (confirmed)
      result = await updateOrderShippingAddress(order.value.orderNo, { ...payload, confirm_delivery_change: true });
  }

  if (result.success) {
    toast.add({
      title: "Shipping address updated",
      description: "The order delivery address was saved.",
      color: "success",
    });
    isEditingAddress.value = false;
    await loadOrder();
  }
  else {
    toast.add({
      title: "Address update failed",
      description: result.error || "Could not update shipping address.",
      color: "error",
    });
  }

  isSavingAddress.value = false;
}

async function submitOrderNote() {
  if (!order.value?.orderNo)
    return;
  if (!noteForm.message.trim()) {
    toast.add({
      title: "Note is empty",
      description: "Enter a note before saving.",
      color: "warning",
    });
    return;
  }

  isSavingNote.value = true;
  const result = await addOrderNote(order.value.orderNo, {
    message: noteForm.message.trim(),
    note_type: noteForm.note_type.trim() || "Admin",
  });

  if (result.success) {
    noteForm.message = "";
    noteForm.note_type = "Admin";
    toast.add({
      title: "Note added",
      description: "The order note was saved.",
      color: "success",
    });
    await refreshOrderNotes();
  }
  else {
    toast.add({
      title: "Note failed",
      description: result.error || "Could not add order note.",
      color: "error",
    });
  }

  isSavingNote.value = false;
}

async function openLineDetail(product: any) {
  if (!order.value?.orderNo || !product?.id)
    return;

  selectedLine.value = null;
  isLineDetailOpen.value = true;
  isLoadingLine.value = true;
  const result = await getOrderLine(order.value.orderNo, product.id);

  if (result.success) {
    selectedLine.value = result.data;
  }
  else {
    toast.add({
      title: "Could not load line detail",
      description: result.error || "Please try again.",
      color: "error",
    });
    isLineDetailOpen.value = false;
  }

  isLoadingLine.value = false;
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
      class="h-8 w-8 animate-spin text-slate-500"
      />
    </div>

    <div v-else-if="order" class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
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
          <div>
            <h1 class="truncate text-2xl font-black tracking-tight text-slate-950">
            {{ order.orderNo }}
            </h1>
            <p class="mt-1 text-sm text-slate-500">
              Created {{ formatDate(order.createdDate) }}
            </p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-3">
        <div class="space-y-6 lg:col-span-2">
          <Stepper :steps="orderSteps" />

          <UCard class="border border-slate-200 bg-white shadow-sm">
            <template #header>
              <h3 class="text-lg font-bold text-slate-950">Order details</h3>
            </template>

            <div class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <div class="mb-1 text-sm text-slate-500">
                    Created
                  </div>
                  <div class="font-semibold tracking-tight text-slate-950">
                    {{ formatDate(order.createdDate) }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-slate-500">Total</div>
                  <div class="font-semibold tracking-tight text-slate-950">
                    {{ formatMoney(order.orderTotal, "KES") }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-slate-500">
                    Order Via
                  </div>
                  <div class="font-semibold tracking-tight text-slate-950">
                    {{ order.orderVia }}
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-sm text-slate-500">
                    Order Stage
                  </div>
                  <UBadge
                    :color="statusColor(order.status)"
                    variant="soft"
                    size="lg"
                    class="capitalize"
                  >
                    {{ order.status }}
                  </UBadge>
                </div>
              </div>

              <div>
                <h4 class="mb-3 text-base font-semibold text-slate-950">
                  <UIcon
                    name="i-lucide-map-pin"
                    class="mr-2 inline h-4 w-4 text-primary"
                  />
                  Shipping Information
                </h4>
                <div class="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div class="font-medium tracking-tight text-slate-950">
                      <template v-if="order.shippingAddress">
                        <span>{{ order.shippingAddress.firstName }} {{ order.shippingAddress.lastName }}</span><br>
                        <span>{{ order.shippingAddress.street || order.shippingAddress.line1 }}</span><br>
                        <span>
                          {{ order.shippingAddress.city }},
                          {{ order.shippingAddress.state }}
                          {{ order.shippingAddress.zipCode }}
                        </span>
                        <div v-if="order.shippingAddress.phoneNumber" class="mt-2 text-sm text-slate-600">
                          Phone: {{ order.shippingAddress.phoneNumber }}
                        </div>
                        <div v-if="order.shippingAddress.notes" class="mt-2 text-sm text-slate-600">
                          Delivery notes: {{ order.shippingAddress.notes }}
                        </div>
                        <div v-if="order.shippingAddress.location" class="mt-2 text-sm text-slate-600">
                          Pin: {{ order.shippingAddress.location.latitude }}, {{ order.shippingAddress.location.longitude }}
                          <span v-if="order.shippingAddress.location.label">· {{ order.shippingAddress.location.label }}</span>
                        </div>
                      </template>
                      <template v-else>No shipping address provided</template>
                    </div>
                    <UButton color="neutral" variant="outline" size="sm" @click="isEditingAddress = !isEditingAddress">
                      <UIcon :name="isEditingAddress ? 'i-lucide-x' : 'i-lucide-pencil'" />
                      {{ isEditingAddress ? "Cancel" : "Edit address" }}
                    </UButton>
                  </div>

                  <div v-if="isEditingAddress" class="rounded-lg border border-slate-200 bg-white p-4">
                    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <UFormField label="First name" required><UInput v-model="shippingForm.first_name" /></UFormField>
                      <UFormField label="Last name" required><UInput v-model="shippingForm.last_name" /></UFormField>
                      <UFormField label="Address line 1" required class="md:col-span-2"><UInput v-model="shippingForm.line1" /></UFormField>
                      <UFormField label="Address line 2"><UInput v-model="shippingForm.line2" /></UFormField>
                      <UFormField label="Company / line 3"><UInput v-model="shippingForm.line3" /></UFormField>
                      <UFormField label="City" required><UInput v-model="shippingForm.line4" /></UFormField>
                      <UFormField label="State / county"><UInput v-model="shippingForm.state" /></UFormField>
                      <UFormField label="Postcode"><UInput v-model="shippingForm.postcode" /></UFormField>
                      <UFormField label="Country code"><UInput v-model="shippingForm.country_code" maxlength="2" /></UFormField>
                      <UFormField label="Phone"><UInput v-model="shippingForm.phone_number" /></UFormField>
                      <UFormField label="Delivery notes" class="md:col-span-2"><UTextarea v-model="shippingForm.notes" :rows="3" /></UFormField>
                      <UFormField label="Latitude"><UInput v-model="shippingForm.latitude" placeholder="-1.292066" /></UFormField>
                      <UFormField label="Longitude"><UInput v-model="shippingForm.longitude" placeholder="36.821946" /></UFormField>
                      <UFormField label="Location label" class="md:col-span-2"><UInput v-model="shippingForm.location_label" placeholder="Main gate, site entrance, shop front" /></UFormField>
                    </div>
                    <div class="mt-4 flex justify-end">
                      <UButton color="primary" variant="solid" :loading="isSavingAddress" @click="submitShippingAddress">
                        Save address
                      </UButton>
                    </div>
                  </div>

                  <iframe
                    v-if="order.shippingAddress"
                    class="h-56 w-full rounded-lg border border-slate-200"
                    style="min-height:224px"
                    :src="googleMapsUrl"
                    allowfullscreen
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"
                  />
                  <div v-if="googleMapsLink" class="flex justify-end">
                    <UButton :to="googleMapsLink" target="_blank" color="neutral" variant="outline" size="sm">
                      <UIcon name="i-lucide-map" />
                      Open in Google Maps
                    </UButton>
                  </div>
                </div>
              </div>

              <div>
                <h4 class="mb-3 text-base font-semibold text-slate-950">
                  Products
                </h4>
                <div class="space-y-4">
                  <div
                    v-for="product in order.products"
                    :key="product.id"
                    class="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4"
                  >
                    <img
                      v-if="product.image"
                      :src="mediaUrl(product.image)"
                      :alt="product.name"
                      class="h-14 w-14 rounded-lg border border-slate-200 object-cover"
                    >
                    <div
                      v-else
                      class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-400"
                    >
                      <UIcon name="i-lucide-image-off" class="size-5" />
                    </div>
                    <div class="flex-1">
                      <div class="font-semibold text-slate-950">
                        {{ product.name }}
                      </div>
                      <div class="text-sm text-slate-500">
                        Qty: {{ product.quantity }}
                      </div>
                    </div>
                    <div class="font-semibold text-slate-950">
                      {{ formatMoney(product.price || 0, "KES") }}
                    </div>
                    <UTooltip text="View line detail">
                      <UButton
                        icon="i-lucide-panel-right-open"
                        color="neutral"
                        variant="ghost"
                        square
                        @click="openLineDetail(product)"
                      />
                    </UTooltip>
                  </div>
                </div>
              </div>

              <div class="border-t border-slate-200 pt-4">
                <div class="space-y-2">
                  <div class="flex justify-between">
                    <span class="text-slate-500">Subtotal</span>
                    <span class="text-slate-950">{{ formatMoney(order.subtotal || 0, "KES") }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-500">Shipping</span>
                    <span class="text-slate-950">{{ formatMoney(order.shipping || 0, "KES") }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-500">Tax</span>
                    <span class="text-slate-950">{{ formatMoney(order.tax || 0, "KES") }}</span>
                  </div>
                  <div class="flex justify-between border-t border-slate-200 pt-2 text-lg font-bold text-slate-950">
                    <span>Total</span>
                    <span>{{ formatMoney(order.orderTotal, "KES") }}</span>
                  </div>
                </div>
              </div>
            </div>
          </UCard>
        </div>

        <div class="space-y-6">
          <UCard class="border border-slate-200 bg-white shadow-sm">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-settings-2" class="h-5 w-5 text-slate-950" />
                <h3 class="text-lg font-bold text-slate-950">Admin actions</h3>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-950">Order status</label>
                  <USelect
                    v-model="statusForm.status"
                    :items="statusOptions"
                    value-attribute="value"
                    option-attribute="label"
                    size="lg"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-950">Tracking reference</label>
                  <UInput
                    v-model="statusForm.tracking_reference"
                    size="lg"
                    placeholder="TRK-1001"
                  />
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-950">Internal note</label>
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

          <UCard class="border border-slate-200 bg-white shadow-sm">
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-sticky-note" class="h-5 w-5 text-slate-950" />
                  <h3 class="text-lg font-bold text-slate-950">Order notes</h3>
                </div>
                <UBadge color="neutral" variant="soft">{{ order.notes?.length || 0 }}</UBadge>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
                <UFormField label="Type">
                  <UInput v-model="noteForm.note_type" placeholder="Admin" />
                </UFormField>
                <UFormField label="Message" class="md:col-span-2">
                  <UTextarea v-model="noteForm.message" :rows="3" placeholder="Add an internal order note..." />
                </UFormField>
              </div>
              <div class="flex justify-end">
                <UButton color="primary" variant="solid" :loading="isSavingNote" @click="submitOrderNote">
                  Add note
                </UButton>
              </div>

              <div v-if="!order.notes?.length" class="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">
                No order notes recorded.
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="note in order.notes"
                  :key="note.id"
                  class="rounded-lg border border-slate-200 bg-slate-50 p-4"
                >
                  <div class="mb-2 flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="font-semibold text-slate-950">{{ note.note_type || "Note" }}</p>
                      <p class="text-xs text-slate-500">
                        {{ note.author || "System" }} · {{ formatDateTime(note.date_created) }}
                      </p>
                    </div>
                  </div>
                  <p class="whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ note.message }}</p>
                </div>
              </div>
            </div>
          </UCard>

          <UCard class="border border-slate-200 bg-white shadow-sm">
            <template #header>
              <h3 class="text-lg font-bold text-slate-950">Customer</h3>
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
                    class="absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-white bg-emerald-500"
                  />
                </div>
                <div>
                  <div class="font-semibold text-slate-950">
                    {{ order.customer?.name || order.companyName }}
                  </div>
                  <div class="text-sm text-slate-500">
                    {{ order.customer?.company || order.companyName }}
                  </div>
                </div>
              </div>

              <div class="space-y-3">
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-mail" class="h-4 w-4 text-slate-500" />
                  <div>
                    <div class="text-sm text-slate-500">Email</div>
                    <div class="font-medium tracking-tight text-slate-950">
                      {{ order.customer?.email || "No email available" }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-phone" class="h-4 w-4 text-slate-500" />
                  <div>
                    <div class="text-sm text-slate-500">Phone</div>
                    <div class="font-medium tracking-tight text-slate-950">
                      {{ order.customer?.phone || "No phone available" }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <UIcon name="i-lucide-building" class="h-4 w-4 text-slate-500" />
                  <div>
                    <div class="text-sm text-slate-500">Company</div>
                    <div class="font-medium tracking-tight text-slate-950">
                      {{ order.customer?.company || order.companyName }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <UCard class="border border-slate-200 bg-white shadow-sm">
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-truck" class="h-5 w-5 text-slate-950" />
                  <h3 class="text-lg font-bold text-slate-950">Tracking</h3>
                </div>
                <div class="flex flex-col items-end gap-1">
                  <div class="text-sm text-slate-500">
                    <span>Status : </span>
                    <span class="font-medium text-slate-950">{{ order.status }}</span>
                  </div>
                </div>
              </div>
            </template>

            <div class="relative pl-8">
              <div
                class="absolute bottom-0 left-3 top-0 w-px border-l-2 border-dashed border-slate-200"
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
                    <div class="font-medium text-slate-950">
                      {{ item.status }} ({{ formatTime(item.date) }})
                    </div>
                    <div class="text-sm text-slate-500">
                      {{ item.location }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <UCard v-if="order.supplierGroups?.length" class="border border-slate-200 bg-white shadow-sm">
            <template #header>
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-boxes" class="h-5 w-5 text-slate-950" />
                  <h3 class="text-lg font-bold text-slate-950">Supplier Groups</h3>
                </div>
            </template>

            <div class="space-y-4">
              <div
                v-for="group in order.supplierGroups"
                :key="group.id"
                class="rounded-lg border border-slate-200 p-4"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <div>
                    <div class="font-medium text-slate-950">{{ group.name }}</div>
                    <div class="text-sm text-slate-500">
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
                <div class="space-y-1 text-sm text-slate-500">
                  <div v-if="group.trackingReference">
                    Tracking: <span class="font-medium text-slate-950">{{ group.trackingReference }}</span>
                  </div>
                  <div v-if="group.notes">
                    Note: <span class="font-medium text-slate-950">{{ group.notes }}</span>
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
          class="mx-auto mb-4 h-12 w-12 text-slate-400"
        />
        <p class="text-slate-950">Order not found</p>
      </div>
    </div>

    <div v-if="isLineDetailOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[90vh] w-full max-w-2xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-default">Order line detail</h3>
              <p class="truncate text-sm text-dimmed">{{ selectedLine?.title || "Loading line information" }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="isLineDetailOpen = false" />
          </div>
        </template>

        <div v-if="isLoadingLine" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading line detail
        </div>

        <div v-else-if="selectedLine" class="space-y-5">
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-lg font-black text-slate-950">{{ selectedLine.title }}</p>
                <p class="mt-1 text-sm text-slate-500">Line #{{ selectedLine.id }}</p>
              </div>
              <UBadge :color="statusColor(selectedLine.status)" variant="soft">
                {{ selectedLine.status || "No status" }}
              </UBadge>
            </div>
          </div>

          <dl class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-lg border border-slate-200 p-4">
              <dt class="text-sm font-semibold text-slate-500">Quantity</dt>
              <dd class="mt-1 text-slate-950">{{ selectedLine.quantity }}</dd>
            </div>
            <div class="rounded-lg border border-slate-200 p-4">
              <dt class="text-sm font-semibold text-slate-500">UPC</dt>
              <dd class="mt-1 break-words text-slate-950">{{ selectedLine.upc || "Not recorded" }}</dd>
            </div>
            <div class="rounded-lg border border-slate-200 p-4">
              <dt class="text-sm font-semibold text-slate-500">Partner</dt>
              <dd class="mt-1 break-words text-slate-950">{{ selectedLine.partner_name || "Not recorded" }}</dd>
            </div>
            <div class="rounded-lg border border-slate-200 p-4">
              <dt class="text-sm font-semibold text-slate-500">Partner SKU</dt>
              <dd class="mt-1 break-words text-slate-950">{{ selectedLine.partner_sku || "Not recorded" }}</dd>
            </div>
          </dl>

          <div class="overflow-hidden rounded-lg border border-slate-200">
            <div class="grid grid-cols-3 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
              <div>Amount</div>
              <div class="text-right">Excl tax</div>
              <div class="text-right">Incl tax</div>
            </div>
            <div class="grid grid-cols-3 border-t border-slate-100 px-4 py-3 text-sm">
              <div class="font-semibold text-slate-700">Unit price</div>
              <div class="text-right text-slate-950">{{ formatMoney(selectedLine.unit_price_excl_tax || 0, selectedLine.currency || "KES") }}</div>
              <div class="text-right text-slate-950">{{ formatMoney(selectedLine.unit_price_incl_tax || 0, selectedLine.currency || "KES") }}</div>
            </div>
            <div class="grid grid-cols-3 border-t border-slate-100 px-4 py-3 text-sm">
              <div class="font-semibold text-slate-700">Line total</div>
              <div class="text-right text-slate-950">{{ formatMoney(selectedLine.line_price_excl_tax || 0, selectedLine.currency || "KES") }}</div>
              <div class="text-right text-slate-950">{{ formatMoney(selectedLine.line_price_incl_tax || 0, selectedLine.currency || "KES") }}</div>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end">
            <UButton color="neutral" variant="outline" @click="isLineDetailOpen = false">Close</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
