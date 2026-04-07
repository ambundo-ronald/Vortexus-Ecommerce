import type { TableColumn } from "@nuxt/ui";
import type { ProductTableRow } from "~/types/ProductTableRow";
import { useSortableHeader } from "~/composables/useSortableHeader";
import type { SortBy, SortDir } from "~/types/Table";

export function getProductTableColumns({
  sortBy,
  sortDir,
  components,
}: {
  sortBy: Ref<SortBy>;
  sortDir: Ref<SortDir>;
  components: unknown[];
}): TableColumn<ProductTableRow>[] {
  const [UButton, UBadge, UCheckbox, UAvatar] = components;
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
      accessorKey: "id",
      header: ({ column }) => renderSortableHeader("Product #", column),
      cell: ({ row }) =>
        h("span", { class: "font-mono" }, `#${row.original.id}`),
    },
    {
      accessorKey: "name",
      header: ({ column }) => renderSortableHeader("Product", column),
      cell: ({ row }) =>
        h("div", { class: "min-w-50 flex items-center gap-3" }, [
          h(UAvatar as Component, {
            src: row.original.imageUrl,
            alt: row.original.name,
            size: "xs",
            imgClass: "object-cover",
            onError: (e: Event) => {
              const target = e.target as HTMLImageElement;
              target.src =
                "https://placehold.co/400x400/64748b/ffffff?text=N/A";
            },
          }),
          h("span", { class: "font-medium text-default" }, row.original.name),
        ]),
    },
    {
      accessorKey: "sku",
      header: ({ column }) => renderSortableHeader("SKU", column),
      cell: ({ row }) => h("span", { class: "font-mono" }, row.original.sku),
    },
    {
      accessorKey: "category",
      header: ({ column }) => renderSortableHeader("Category", column),
      cell: ({ row }) => row.original.category,
    },
    {
      accessorKey: "status",
      header: ({ column }) => renderSortableHeader("Status", column),
      cell: ({ row }) => {
        const statusMap: Record<string, string> = {
          Active: "success",
          Draft: "warning",
          Archived: "danger",
        };
        const color = statusMap[row.original.status] || "neutral";
        return h(UBadge as any, {
          label: row.original.status,
          color,
          variant: "soft",
        });
      },
    },
    {
      accessorKey: "stock",
      header: ({ column }) => renderSortableHeader("Stock", column),
      cell: ({ row }) => {
        const stock = row.original.stock;
        const color =
          stock > 50 ? "success" : stock > 10 ? "warning" : "danger";
        return h(UBadge as Component, {
          label: stock.toString(),
          color,
          variant: "soft",
        });
      },
    },
    {
      accessorKey: "price",
      header: ({ column }) => renderSortableHeader("Price", column),
      cell: ({ row }) => `$${Number(row.getValue("price") ?? 0).toFixed(2)}`,
    },
  ];
}
