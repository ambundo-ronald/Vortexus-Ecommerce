<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

export interface Order {
  id: number;
  customer: string;
  date: string;
  total: number;
  status: 'Paid' | 'Pending' | 'Failed';
}

defineProps<{
  orders: Order[];
}>();

const columns: TableColumn<Order>[] = [
  {
    accessorKey: 'id',
    header: 'Order',
    cell: (ctx) => `#${ctx.row.getValue('id')}`
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: (ctx) => ctx.row.getValue('customer')
  },
  {
    accessorKey: 'date',
    header: 'Date',
    cell: (ctx) => {
      return new Date(ctx.row.getValue('date')).toLocaleString('en-US', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    }
  },
  {
    accessorKey: 'total',
    header: 'Total',
    cell: (ctx) => `${ctx.row.getValue('total')}`
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: (ctx) => {
      const status = ctx.row.getValue('status') as Order['status'];
      return h(
        resolveComponent('UBadge'),
        {
          label: status,
          color: status === 'Paid' ? 'success' : status === 'Pending' ? 'warning' : 'error'
        }
      );
    }
  }
];
</script>
<template>
  <UCard class="w-full">
    <div class="flex items-center justify-between">
      <h3 class="text-base font-semibold text-highlighted">Latest Orders</h3>
    </div>
    <UTable
      :columns="columns"
      :data="orders"
      :ui="{ root: 'bg-transparent dark:bg-transparent !border-hidden dark:border-hidden' }"
    >
      <template #id="{ row }">
        #{{ row.id }}
      </template>
      <template #status="{ row }">
        <UBadge
          :label="row.status"
          :color="row.status === 'Paid' ? 'success' : row.status === 'Pending' ? 'warning' : 'error'"
        />
      </template>
    </UTable>
  </UCard>
</template>
