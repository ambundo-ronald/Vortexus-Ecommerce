import type { TableColumn } from "@nuxt/ui";
import type { UserTableRow } from "~/types/UserTableRow";
import { useSortableHeader } from "~/composables/useSortableHeader";
import type { SortBy, SortDir } from "~/types/Table";

export function getUserTableColumns({
  onEdit,
  sortBy,
  sortDir,
  components,
}: {
  onEdit: (user: UserTableRow, event?: Event) => void;
  sortBy: Ref<SortBy>;
  sortDir: Ref<SortDir>;
  components: Component[];
}): TableColumn<UserTableRow>[] {
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
      accessorKey: "name",
      header: ({ column }) => renderSortableHeader("User", column),
      cell: ({ row }) =>
        h("div", { class: "flex items-center gap-3" }, [
          h(UAvatar as Component, {
            src: row.original.imageUrl,
            alt: row.original.name,
            size: "xs",
            imgClass: "object-cover",
            onError: (e: Event) => {
              const target = e.target as HTMLImageElement;
              target.src = "https://placehold.co/400x400/64748b/ffffff?text=N/A";
            },
          }),
          h("span", { class: "font-medium text-default" }, row.original.name),
        ]),
    },
    {
      accessorKey: "email",
      header: ({ column }) => renderSortableHeader("Email", column),
      cell: ({ row }) => row.original.email,
    },
    {
      accessorKey: "role",
      header: ({ column }) => renderSortableHeader("Role", column),
      cell: ({ row }) => row.original.role,
    },
    {
      accessorKey: "status",
      header: ({ column }) => renderSortableHeader("Status", column),
      cell: ({ row }) => {
        const statusMap: Record<string, string> = {
          Active: "success",
          Suspended: "error",
        };
        const color =
          statusMap[row.original.status as keyof typeof statusMap] || "neutral";
        return h(UBadge as Component, {
          label: row.original.status,
          color,
          variant: "soft",
        });
      },
    },
    {
      accessorKey: "joined",
      header: ({ column }) => renderSortableHeader("Joined", column),
      cell: ({ row }) => row.original.joined,
    },
    {
      id: "actions",
      header: () => h("span", { class: "sr-only" }, "Actions"),
      cell: ({ row }) =>
        h("div", { class: "flex items-center justify-end gap-2" }, [
          h(UButton as Component, {
            icon: "i-lucide-pencil",
            color: "neutral",
            variant: "ghost",
            size: "xs",
            "aria-label": `Edit ${row.original.name}`,
            onClick: (event: Event) => {
              event.stopPropagation();
              onEdit(row.original, event);
            },
          }),
        ]),
    },
  ];
}
