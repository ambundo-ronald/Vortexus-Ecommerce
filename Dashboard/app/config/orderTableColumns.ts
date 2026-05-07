import type { TableColumn } from "@nuxt/ui";
import type { OrderTableRow } from "~/types/OrderTableRow";
import { useSortableHeader } from "~/composables/useSortableHeader";
import type { SortBy, SortDir } from "~/types/Table";
import { formatMoney } from "~/utils/media";

function orderStatusColor(status: string) {
  const normalized = String(status || "").toLowerCase();

  if (["paid", "delivered", "complete", "completed"].includes(normalized))
    return "success";
  if (["packed", "shipped", "processing"].includes(normalized))
    return "primary";
  if (["failed", "cancelled", "canceled"].includes(normalized))
    return "error";
  if (["pending"].includes(normalized))
    return "warning";

  return "neutral";
}

function booleanIcon(value: boolean) {
  return {
    name: value ? "i-lucide-check" : "i-lucide-minus",
    class: value ? "size-4 text-emerald-600" : "size-4 text-slate-300",
  };
}

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
      cell: ({ row }) =>
        h("span", { class: "font-mono text-sm font-semibold text-slate-950" }, row.original.orderNo),
    },
    {
      accessorKey: "companyName",
      header: ({ column }) => renderSortableHeader("Company", column),
      cell: ({ row }) =>
        h(
          "div",
          { class: "max-w-52 truncate font-medium text-slate-950" },
          `${row.getValue("companyName") || "Customer"}`
        ),
    },
    {
      accessorKey: "status",
      header: ({ column }) => renderSortableHeader("Status", column),
      cell: ({ row }) => {
        return h(UBadge as Component, {
          label: row.original.status,
          color: orderStatusColor(row.original.status),
          variant: "soft",
          class: "capitalize",
        });
      },
    },
    {
      accessorKey: "packaged",
      header: ({ column }) => renderSortableHeader("Packaged", column),
      cell: ({ row }) =>
        h(UIcon as Component, booleanIcon(Boolean(row.getValue("packaged")))),
    },
    {
      accessorKey: "fulfilled",
      header: ({ column }) => renderSortableHeader("Fulfilled", column),
      cell: ({ row }) =>
        h(UIcon as Component, booleanIcon(Boolean(row.getValue("fulfilled")))),
    },
    {
      accessorKey: "invoiced",
      header: ({ column }) => renderSortableHeader("Invoiced", column),
      cell: ({ row }) =>
        h(UIcon as Component, booleanIcon(Boolean(row.getValue("invoiced")))),
    },
    {
      accessorKey: "paid",
      header: ({ column }) => renderSortableHeader("Paid", column),
      cell: ({ row }) =>
        h(UIcon as Component, booleanIcon(Boolean(row.getValue("paid")))),
    },
    {
      accessorKey: "orderTotal",
      header: ({ column }) => renderSortableHeader("Order Total", column),
      cell: ({ row }) =>
        h("span", { class: "font-semibold text-slate-950" }, formatMoney(row.getValue("orderTotal") ?? 0, "KES")),
    },
    {
      accessorKey: "createdDate",
      header: ({ column }) => renderSortableHeader("Date", column),
      cell: ({ row }) =>
        h("span", { class: "text-sm text-slate-600" }, new Date(row.getValue("createdDate")).toLocaleDateString()),
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
