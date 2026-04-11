<script setup lang="ts">
import { getUserTableColumns } from "~/config/userTableColumns";
import type { SortBy, SortDir } from "~/types/Table";
import type { UserTableRow } from "~/types/UserTableRow";

const UBadge = resolveComponent("UBadge");
const UButton = resolveComponent("UButton");
const UInput = resolveComponent("UInput");
const UAvatar = resolveComponent("UAvatar");
const UCheckbox = resolveComponent("UCheckbox");

const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");
const userData = ref<UserTableRow[]>([]);
const totalItems = ref(0);
const isLoading = ref(false);
const isSaving = ref(false);
const editingUserId = ref<string | null>(null);
const isEditorOpen = ref(false);
const summary = ref({
  total: 0,
  active: 0,
  suspended: 0,
  staff: 0,
});

const userForm = reactive({
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  company: "",
  role: "customer",
  status: "active",
  password: "",
  isSupplier: false,
});

const roleOptions = [
  { label: "All roles", value: "" },
  { label: "Customer", value: "customer" },
  { label: "Supplier", value: "supplier" },
  { label: "Staff", value: "staff" },
  { label: "Admin", value: "admin" },
];

const editableRoleOptions = [
  { label: "Customer", value: "customer" },
  { label: "Staff", value: "staff" },
  { label: "Admin", value: "admin" },
];

const statusOptions = [
  { label: "All statuses", value: "" },
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
];

const editableStatusOptions = [
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
];

const { createUser, getUser, getUsers, updateUser } = useUser();
const toast = useToast();

const columns = getUserTableColumns({
  onEdit: (user) => openEditUser(user),
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UAvatar] as Component[],
});

function resetForm() {
  editingUserId.value = null;
  userForm.email = "";
  userForm.first_name = "";
  userForm.last_name = "";
  userForm.phone = "";
  userForm.company = "";
  userForm.role = "customer";
  userForm.status = "active";
  userForm.password = "";
  userForm.isSupplier = false;
}

async function loadUsers() {
  isLoading.value = true;
  const result = await getUsers({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    role: roleFilter.value,
    status: statusFilter.value,
    sortBy: sortBy.value,
  });

  if (result.success) {
    userData.value = result.data?.results ?? [];
    totalItems.value = result.data?.pagination?.total ?? 0;
    summary.value = result.data?.summary ?? summary.value;
  }
  else {
    userData.value = [];
    totalItems.value = 0;
    summary.value = { total: 0, active: 0, suspended: 0, staff: 0 };
    toast.add({
      title: "Could not load users",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
  isLoading.value = false;
}

function openCreateUser() {
  resetForm();
  isEditorOpen.value = true;
}

async function openEditUser(user: UserTableRow) {
  resetForm();
  editingUserId.value = user.id;
  isEditorOpen.value = true;

  const result = await getUser(user.id);
  if (result.success) {
    const data = result.data;
    userForm.email = data.email;
    userForm.first_name = data.first_name;
    userForm.last_name = data.last_name;
    userForm.phone = data.phone;
    userForm.company = data.company;
    userForm.role = data.role;
    userForm.status = data.status;
    userForm.isSupplier = data.isSupplier;
  }
  else {
    isEditorOpen.value = false;
    toast.add({
      title: "Could not load user",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
}

async function submitUserForm() {
  isSaving.value = true;
  const payload = {
    email: userForm.email,
    first_name: userForm.first_name,
    last_name: userForm.last_name,
    phone: userForm.phone,
    company: userForm.company,
    role: userForm.isSupplier ? undefined : userForm.role,
    status: userForm.status,
    password: userForm.password || undefined,
  };
  const result = editingUserId.value
    ? await updateUser(editingUserId.value, payload)
    : await createUser(payload);

  if (result.success) {
    toast.add({
      title: editingUserId.value ? "User updated" : "User created",
      description: `${userForm.email} was saved successfully.`,
      color: "success",
    });
    isEditorOpen.value = false;
    resetForm();
    await loadUsers();
  }
  else {
    toast.add({
      title: "Save failed",
      description: result.error || "Could not save user.",
      color: "error",
    });
  }

  isSaving.value = false;
}

watch([currentPage, pageSize, searchQuery, roleFilter, statusFilter, sortBy, sortDir], loadUsers, { immediate: true });
watch([searchQuery, roleFilter, statusFilter, pageSize], () => {
  currentPage.value = 1;
});
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between p-8 pb-4">
      <h1 class="text-xl font-semibold">Users</h1>

      <div class="flex w-full items-center justify-end gap-2">
        <UInput
          v-model="searchQuery"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search users..."
          :ui="{ leadingIcon: 'size-4' }"
        />

        <USelect
          v-model="roleFilter"
          :items="roleOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          size="lg"
        />

        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          size="lg"
        />

        <UButton variant="outline" :loading="isLoading" @click="loadUsers">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateUser">
          <UIcon name="i-lucide-plus" />
          Add User
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-8 px-8 sm:grid-cols-2 lg:grid-cols-4">
      <CardsKpiCard2
        name="Total Users"
        :value="summary.total"
        :budget="summary.total"
        color="var(--color-info)"
        icon="i-lucide-users"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Active"
        :value="summary.active"
        :budget="summary.total"
        color="var(--color-success)"
        icon="i-lucide-user-check"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Suspended"
        :value="summary.suspended"
        :budget="summary.total"
        color="var(--color-error)"
        icon="i-lucide-user-x"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Staff"
        :value="summary.staff"
        :budget="summary.total"
        color="var(--color-warning)"
        icon="i-lucide-shield"
        :loading="isLoading"
      />
    </div>

    <div class="px-8">
      <UTable
        class="cursor-pointer"
        :data="userData"
        :columns="columns"
        :loading="isLoading"
        @select="(user) => openEditUser(user)"
      />
      <div class="flex justify-end pt-4">
        <UPagination
          :page="currentPage"
          :page-count="pageSize"
          :total="totalItems"
          @update:page="(page: number) => currentPage = page"
        />
      </div>
    </div>

    <div
      v-if="isEditorOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">
                {{ editingUserId ? "Edit user" : "Add user" }}
              </h3>
              <p class="text-sm text-dimmed">
                Manage account access and profile basics.
              </p>
            </div>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              square
              @click="isEditorOpen = false"
            />
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Email" required>
            <UInput v-model="userForm.email" type="email" />
          </UFormField>
          <UFormField :label="editingUserId ? 'New password' : 'Password'" :required="!editingUserId">
            <UInput v-model="userForm.password" type="password" />
          </UFormField>
          <UFormField label="First name">
            <UInput v-model="userForm.first_name" />
          </UFormField>
          <UFormField label="Last name">
            <UInput v-model="userForm.last_name" />
          </UFormField>
          <UFormField label="Phone">
            <UInput v-model="userForm.phone" />
          </UFormField>
          <UFormField label="Company">
            <UInput v-model="userForm.company" />
          </UFormField>
          <UFormField label="Role">
            <USelect
              v-model="userForm.role"
              :items="editableRoleOptions"
              value-attribute="value"
              option-attribute="label"
              :disabled="userForm.isSupplier"
            />
            <p v-if="userForm.isSupplier" class="mt-1 text-xs text-dimmed">
              Supplier role is managed through supplier onboarding.
            </p>
          </UFormField>
          <UFormField label="Status">
            <USelect
              v-model="userForm.status"
              :items="editableStatusOptions"
              value-attribute="value"
              option-attribute="label"
            />
          </UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              color="neutral"
              variant="outline"
              :disabled="isSaving"
              @click="isEditorOpen = false"
            >
              Cancel
            </UButton>
            <UButton
              color="primary"
              variant="solid"
              :loading="isSaving"
              @click="submitUserForm"
            >
              Save user
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
