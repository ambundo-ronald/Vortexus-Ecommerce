<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

const { getSupportQueue, updateCallback } = useSupport();
const toast = useToast();

const isLoading = ref(false);
const summary = ref<any | null>(null);
const selectedTicket = ref<any | null>(null);
const callbackNotes = ref("");
const isUpdating = ref(false);

const ticketColumns: TableColumn<any>[] = [
  {
    accessorKey: "subject",
    header: "Case",
    cell: ({ row }) => h("button", {
      class: "text-left",
      onClick: () => {
        selectedTicket.value = row.original;
      },
    }, [
      h("p", { class: "font-medium text-default" }, row.original.subject),
      h("p", { class: "text-xs text-muted" }, `${row.original.customer} · ${row.original.source}`),
    ]),
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: row.original.type,
      color: row.original.type === "callback" ? "success" : row.original.type === "quote" ? "info" : "warning",
      variant: "soft",
    }),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: row.original.status || "Pending",
      color: statusColor(row.original.status),
      variant: "subtle",
    }),
  },
  { accessorKey: "reference", header: "Reference" },
  {
    accessorKey: "respond_by",
    header: "Respond by",
    cell: ({ row }) => row.original.type === "callback"
      ? h("span", { class: row.original.is_overdue ? "font-semibold text-error" : "" }, formatDate(row.original.respond_by))
      : "—",
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => formatDate(row.original.created_at),
  },
];

function statusColor(status: string) {
  const normalized = (status || "").toLowerCase();
  if (["sent", "delivered", "complete", "completed", "resolved", "contacted"].includes(normalized))
    return "success";
  if (["failed", "cancelled", "canceled"].includes(normalized))
    return "error";
  return "warning";
}

function formatDate(value: string) {
  if (!value)
    return "";
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadSupport() {
  isLoading.value = true;
  const result = await getSupportQueue(25);
  if (result.success) {
    summary.value = result.data;
    selectedTicket.value = result.data.tickets?.[0] || null;
    callbackNotes.value = selectedTicket.value?.staff_notes || "";
  }
  else {
    toast.add({
      title: "Could not load support queue",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
  isLoading.value = false;
}

watch(selectedTicket, (ticket) => {
  callbackNotes.value = ticket?.staff_notes || "";
});

async function setCallbackStatus(status: string) {
  if (!selectedTicket.value?.callback_id)
    return;
  isUpdating.value = true;
  const result = await updateCallback(selectedTicket.value.callback_id, {
    status,
    staff_notes: callbackNotes.value,
  });
  if (result.success) {
    toast.add({
      title: status === "resolved" ? "Callback lead resolved" : "Callback marked as contacted",
      color: "success",
    });
    await loadSupport();
    selectedTicket.value = summary.value?.tickets?.find((ticket: any) => ticket.callback_id === Number(result.data?.id)) || selectedTicket.value;
  }
  else {
    toast.add({ title: "Could not update callback", description: result.error, color: "error" });
  }
  isUpdating.value = false;
}

onMounted(loadSupport);
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 p-8 pb-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-xl font-semibold">Support</h1>
        <p class="text-sm text-toned">
          Live operational queue from quote notifications and orders that need attention.
        </p>
      </div>
      <UButton variant="outline" :loading="isLoading" @click="loadSupport">
        <UIcon name="i-lucide-refresh-cw" />
        Refresh
      </UButton>
    </div>

    <div class="grid grid-cols-1 gap-6 px-8 md:grid-cols-2 xl:grid-cols-4">
      <UCard>
        <p class="text-sm text-toned">Open cases</p>
        <p class="mt-2 text-3xl font-semibold">{{ summary?.kpis?.open_cases || 0 }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Quote cases</p>
        <p class="mt-2 text-3xl font-semibold">{{ summary?.kpis?.quote_cases || 0 }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Order cases</p>
        <p class="mt-2 text-3xl font-semibold">{{ summary?.kpis?.order_cases || 0 }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Callback leads</p>
        <p class="mt-2 text-3xl font-semibold">{{ summary?.kpis?.callback_leads || 0 }}</p>
        <p v-if="summary?.kpis?.overdue_callbacks" class="mt-1 text-xs font-semibold text-error">
          {{ summary.kpis.overdue_callbacks }} overdue
        </p>
      </UCard>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-8 pb-8 xl:grid-cols-3">
      <UCard class="xl:col-span-2">
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Support Queue</h3>
            <p class="text-sm text-toned">Click a case to inspect its current database context.</p>
          </div>
        </template>
        <UTable
          :columns="ticketColumns"
          :data="summary?.tickets || []"
          :loading="isLoading"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Case Detail</h3>
            <p class="text-sm text-toned">Review the case and record customer follow-up.</p>
          </div>
        </template>

        <div v-if="selectedTicket" class="space-y-4">
          <div>
            <p class="text-xs uppercase text-muted">Subject</p>
            <p class="font-medium">{{ selectedTicket.subject }}</p>
          </div>
          <div>
            <p class="text-xs uppercase text-muted">Customer</p>
            <p>{{ selectedTicket.customer || "Unknown" }}</p>
            <p class="text-sm text-toned">{{ selectedTicket.contact }}</p>
          </div>
          <div>
            <p class="text-xs uppercase text-muted">Message</p>
            <p class="text-sm leading-6">{{ selectedTicket.message }}</p>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p class="text-xs uppercase text-muted">Source</p>
              <p>{{ selectedTicket.source }}</p>
            </div>
            <div>
              <p class="text-xs uppercase text-muted">Reference</p>
              <p>{{ selectedTicket.reference || "N/A" }}</p>
            </div>
            <div>
              <p class="text-xs uppercase text-muted">Status</p>
              <UBadge :label="selectedTicket.status || 'Pending'" :color="statusColor(selectedTicket.status)" variant="subtle" />
            </div>
            <div>
              <p class="text-xs uppercase text-muted">Created</p>
              <p>{{ formatDate(selectedTicket.created_at) }}</p>
            </div>
            <div v-if="selectedTicket.type === 'callback'">
              <p class="text-xs uppercase text-muted">Respond by</p>
              <p :class="{ 'font-semibold text-error': selectedTicket.is_overdue }">
                {{ formatDate(selectedTicket.respond_by) }}
              </p>
            </div>
            <div v-if="selectedTicket.assigned_to">
              <p class="text-xs uppercase text-muted">Assigned to</p>
              <p>{{ selectedTicket.assigned_to }}</p>
            </div>
          </div>
          <div v-if="selectedTicket.type === 'callback'" class="space-y-3 border-t border-default pt-4">
            <UButton :to="`tel:${selectedTicket.contact}`" block color="primary">
              <UIcon name="i-lucide-phone-call" />
              Call {{ selectedTicket.contact }}
            </UButton>
            <UFormField label="Staff notes">
              <UTextarea v-model="callbackNotes" :rows="4" placeholder="Record the outcome or next step..." />
            </UFormField>
            <div class="grid grid-cols-2 gap-2">
              <UButton
                color="warning"
                variant="soft"
                block
                :loading="isUpdating"
                :disabled="selectedTicket.status === 'resolved'"
                @click="setCallbackStatus('contacted')"
              >
                Mark contacted
              </UButton>
              <UButton
                color="success"
                block
                :loading="isUpdating"
                :disabled="selectedTicket.status === 'resolved'"
                @click="setCallbackStatus('resolved')"
              >
                Resolve
              </UButton>
            </div>
          </div>
        </div>

        <div v-else class="rounded-lg border border-dashed border-default p-6 text-center text-sm text-toned">
          No support cases found in the current database.
        </div>
      </UCard>
    </div>
  </div>
</template>
