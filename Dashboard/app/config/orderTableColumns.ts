import type { TableColumn } from "@nuxt/ui";
import type { OrderTableRow } from "~/types/OrderTableRow";
import { useSortableHeader } from "~/composables/useSortableHeader";
import type { SortBy, SortDir } from "~/types/Table";

export function getOrderTableColumns({
  onView,
  sortBy,
  sortDir,
  components,
}: {
  onView: (order: OrderTableRow, event?: Event) => void;
  sortBy: Ref<SortBy>;
  sortDir: Ref<SortDir>;
  components: Component[];
}): TableColumn<OrderTableRow>[] {
  const [UButton, UBadge, UCheckbox, UIcon] = components;
  const { renderSortableHeader } = useSortableHeader(UButton!, sortBy, sortDir);
  return [
    {
      id: "select",
      header: ({ table }) =>
        h(UCheckbox as Component, {
          modelValue: table.getIsSomePageRowsSelected()
            ? "indeterminate"
            : table.getIsAllPageRowsSelected(),
          "onUpdate:modelValue": (value: boolean | "indeterminate") =>
            table.toggleAllPageRowsSelected(!!value),
          "aria-label": "Select all",
        }),
      cell: ({ row }) =>
        h(UCheckbox as Component, {
          modelValue: row.getIsSelected(),
          "onUpdate:modelValue": (value: boolean | "indeterminate") =>
            row.toggleSelected(!!value),
          "aria-label": "Select row",
        }),
    },
    {
      accessorKey: "orderNo",
      header: ({ column }) => renderSortableHeader("Order #", column),
      cell: ({ row }) => h("span", { class: "font-mono" }, row.original.orderNo),
    },
    {
      accessorKey: "companyName",
      header: ({ column }) => renderSortableHeader("Company", column),
      cell: ({ row }) =>
        h(
          "div",
          { class: "font-medium text-default" },
          `${row.getValue("companyName")}`
        ),
    },
    {
      accessorKey: "status",
      header: ({ column }) => renderSortableHeader("Status", column),
      cell: ({ row }) => {
        const statusMap: Record<string, string> = {
          Paid: "success",
          Pending: "warning",
          Processing: "warning",
          Packed: "info",
          Shipped: "info",
          Delivered: "success",
          Cancelled: "error",
          Failed: "danger",
        };
        const color = statusMap[row.original.status] || "neutral";
        return h(UBadge as Component, {
          label: row.original.status,
          color,
          variant: "soft",
        });
      },
    },
    {
      accessorKey: "packaged",
      header: ({ column }) => renderSortableHeader("Packaged", column),
      cell: ({ row }) =>
        h(UIcon as Component, {
          name: row.getValue("packaged") ? "i-lucide-check" : "i-lucide-x",
          class: row.getValue("packaged") ? "text-success" : "text-warning",
        }),
    },
    {
      accessorKey: "fulfilled",
      header: ({ column }) => renderSortableHeader("Fulfilled", column),
      cell: ({ row }) =>
        h(UIcon as Component, {
          name: row.getValue("fulfilled") ? "i-lucide-check" : "i-lucide-x",
          class: row.getValue("fulfilled") ? "text-success" : "text-warning",
        }),
    },
    {
      accessorKey: "invoiced",
      header: ({ column }) => renderSortableHeader("Invoiced", column),
      cell: ({ row }) =>
        h(UIcon as Component, {
          name: row.getValue("invoiced") ? "i-lucide-check" : "i-lucide-x",
          class: row.getValue("invoiced") ? "text-success" : "text-warning",
        }),
    },
    {
      accessorKey: "paid",
      header: ({ column }) => renderSortableHeader("Paid", column),
      cell: ({ row }) =>
        h(UIcon as Component, {
          name: row.getValue("paid") ? "i-lucide-check" : "i-lucide-x",
          class: row.getValue("paid") ? "text-success" : "text-warning",
        }),
    },
    {
      accessorKey: "orderTotal",
      header: ({ column }) => renderSortableHeader("Order Total", column),
      cell: ({ row }) => `${Number(row.getValue("orderTotal") ?? 0).toFixed(2)}`,
    },
    {
      accessorKey: "createdDate",
      header: ({ column }) => renderSortableHeader("Date", column),
      cell: ({ row }) =>
        new Date(row.getValue("createdDate")).toLocaleDateString(),
    },
    {
      id: "actions",
      header: () => h("span", { class: "sr-only" }, "Actions"),
      cell: ({ row }) =>
        h("div", { class: "flex items-center justify-end gap-2" }, [
          h(UButton as Component, {
            icon: "i-lucide-eye",
            color: "neutral",
            variant: "ghost",
            size: "xs",
            "aria-label": `View ${row.original.orderNo}`,
            onClick: (event: Event) => {
              event.stopPropagation();
              onView(row.original, event);
            },
          }),
        ]),
    },
  ];
}
