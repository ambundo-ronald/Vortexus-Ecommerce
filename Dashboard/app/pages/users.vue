<script setup lang="ts">
import { getUserTableColumns } from "~/config/userTableColumns";
import type { SortBy, SortDir } from "~/types/Table";
import type { UserTableRow } from "~/types/UserTableRow";
import type { UserProductAlert } from "~/composables/useUser";

const UBadge = resolveComponent("UBadge");
const UButton = resolveComponent("UButton");
const UInput = resolveComponent("UInput");
const UAvatar = resolveComponent("UAvatar");
const UCheckbox = resolveComponent("UCheckbox");

const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const searchInput = ref("");
const ALL_ROLES = "__all_roles__";
const ALL_STATUSES = "__all_statuses__";
const roleFilter = ref(ALL_ROLES);
const statusFilter = ref(ALL_STATUSES);
const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");
const userData = ref<UserTableRow[]>([]);
const totalItems = ref(0);
const isLoading = ref(false);
const isSaving = ref(false);
const editingUserId = ref<string | null>(null);
const isEditorOpen = ref(false);
const selectedUserDetail = ref<Record<string, any> | null>(null);
const productAlerts = ref<UserProductAlert[]>([]);
const resetPayload = ref<{ uid: string, token: string, email: string } | null>(null);
const saveError = ref("");
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
  { label: "All roles", value: ALL_ROLES },
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
  { label: "All statuses", value: ALL_STATUSES },
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
];

const quickStatusOptions = [
  { label: "Activate", value: "active", icon: "i-lucide-user-check" },
  { label: "Suspend", value: "suspended", icon: "i-lucide-user-x" },
];

const editableStatusOptions = [
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
];

const { cancelUserProductAlert, createUser, generatePasswordReset, getUser, getUserProductAlerts, getUsers, updateUser } = useUser();
const toast = useToast();

const columns = getUserTableColumns({
  onEdit: (user) => openEditUser(user),
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UAvatar] as Component[],
});

function resetForm() {
  editingUserId.value = null;
  selectedUserDetail.value = null;
  productAlerts.value = [];
  resetPayload.value = null;
  saveError.value = "";
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

function normalizeSelectedUser(value: any): UserTableRow {
  return value?.original || value;
}

function formatDate(value?: string) {
  if (!value)
    return "Never";

  return new Intl.DateTimeFormat("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

const activeAlertCount = computed(() => productAlerts.value.filter(alert => alert.status === "Active").length);

function resetConfirmUrl() {
  if (!resetPayload.value)
    return "";
  return `/password-reset/confirm/${resetPayload.value.uid}/${resetPayload.value.token}/`;
}

async function loadUsers() {
  isLoading.value = true;
  const result = await getUsers({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    role: roleFilter.value === ALL_ROLES ? "" : roleFilter.value,
    status: statusFilter.value === ALL_STATUSES ? "" : statusFilter.value,
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

function applySearch() {
  currentPage.value = 1;
  searchQuery.value = searchInput.value.trim();
}

function clearFilters() {
  searchInput.value = "";
  searchQuery.value = "";
  roleFilter.value = ALL_ROLES;
  statusFilter.value = ALL_STATUSES;
  currentPage.value = 1;
}

function openCreateUser() {
  resetForm();
  isEditorOpen.value = true;
}

async function openEditUser(user: UserTableRow) {
  const rowUser = normalizeSelectedUser(user);
  resetForm();
  editingUserId.value = rowUser.id;
  isEditorOpen.value = true;

  const result = await getUser(rowUser.id);
  if (result.success) {
    const data = result.data;
    selectedUserDetail.value = data;
    userForm.email = data.email;
    userForm.first_name = data.first_name;
    userForm.last_name = data.last_name;
    userForm.phone = data.phone;
    userForm.company = data.company;
    userForm.role = data.role;
    userForm.status = data.status;
    userForm.isSupplier = data.isSupplier;
    await loadUserProductAlerts(rowUser.id);
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

async function loadUserProductAlerts(userId = editingUserId.value) {
  if (!userId)
    return;
  const result = await getUserProductAlerts(userId);
  if (result.success)
    productAlerts.value = result.data || [];
  else
    toast.add({ title: "Could not load product alerts", description: result.error || "Please try again.", color: "error" });
}

async function requestPasswordReset() {
  if (!editingUserId.value)
    return;
  isSaving.value = true;
  const result = await generatePasswordReset(editingUserId.value);
  if (result.success && result.data) {
    resetPayload.value = result.data;
    toast.add({ title: "Reset token generated", description: "Use the token payload with the password reset confirm endpoint.", color: "success" });
  }
  else {
    toast.add({ title: "Reset failed", description: result.error || "Could not generate reset token.", color: "error" });
  }
  isSaving.value = false;
}

async function cancelAlert(alert: UserProductAlert) {
  if (!editingUserId.value)
    return;
  const result = await cancelUserProductAlert(editingUserId.value, alert.id);
  if (result.success) {
    toast.add({ title: "Alert cancelled", description: alert.product_title || `Alert #${alert.id}`, color: "success" });
    await loadUserProductAlerts();
  }
  else {
    toast.add({ title: "Could not cancel alert", description: result.error || "Please try again.", color: "error" });
  }
}

async function submitUserForm() {
  saveError.value = "";
  if (!userForm.email.trim()) {
    saveError.value = "Email is required.";
    return;
  }
  if (!editingUserId.value && !userForm.password) {
    saveError.value = "Password is required when creating a user.";
    return;
  }
  if (userForm.password && userForm.password.length < 8) {
    saveError.value = "Password must contain at least 8 characters.";
    return;
  }

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
    saveError.value = result.error || "Could not save user.";
    toast.add({
      title: "Save failed",
      description: result.error || "Could not save user.",
      color: "error",
    });
  }

  isSaving.value = false;
}

async function setUserStatus(status: "active" | "suspended") {
  if (!editingUserId.value)
    return;

  userForm.status = status;
  await submitUserForm();
}

watch([currentPage, pageSize, searchQuery, roleFilter, statusFilter, sortBy, sortDir], loadUsers, { immediate: true });
watch([roleFilter, statusFilter, pageSize], () => {
  currentPage.value = 1;
});
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 p-4 pb-2 sm:p-8 sm:pb-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Users</h1>
        <p class="mt-1 text-sm text-slate-500">Manage dashboard access and customer accounts.</p>
      </div>

      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <form class="flex min-w-56 flex-1 gap-2 lg:max-w-sm" @submit.prevent="applySearch">
          <UInput
            v-model="searchInput"
            class="flex-1"
            color="neutral"
            variant="outline"
            size="lg"
            icon="i-lucide-search"
            placeholder="Search users..."
            :ui="{ leadingIcon: 'size-4' }"
          />
          <UButton color="neutral" variant="outline" type="submit" size="lg">
            Search
          </UButton>
        </form>

        <USelect
          v-model="roleFilter"
          :items="roleOptions"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          value-attribute="value"
          option-attribute="label"
        />

        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />

        <UButton variant="outline" :loading="isLoading" @click="loadUsers">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton variant="ghost" color="neutral" @click="clearFilters">
          Clear
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateUser">
          <UIcon name="i-lucide-plus" />
          Add User
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 px-4 sm:grid-cols-2 sm:px-8 lg:grid-cols-4">
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

    <div class="px-4 sm:px-8">
      <UTable
        class="cursor-pointer"
        :data="userData"
        :columns="columns"
        :loading="isLoading"
        @select="(user) => openEditUser(normalizeSelectedUser(user))"
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
      <UCard class="max-h-[92vh] w-full max-w-4xl overflow-y-auto">
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

        <div v-if="saveError" class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
          {{ saveError }}
        </div>

        <div v-if="selectedUserDetail" class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Joined</p>
            <p class="mt-1 font-semibold text-slate-950">{{ formatDate(selectedUserDetail.dateJoined) }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Last login</p>
            <p class="mt-1 font-semibold text-slate-950">{{ formatDate(selectedUserDetail.lastLogin) }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Access</p>
            <p class="mt-1 font-semibold text-slate-950">
              {{ selectedUserDetail.isSuperuser ? "Super admin" : selectedUserDetail.isStaff ? "Staff" : selectedUserDetail.isSupplier ? "Supplier" : "Customer" }}
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Email" required>
            <UInput v-model="userForm.email" type="email" autocomplete="email" />
          </UFormField>
          <UFormField :label="editingUserId ? 'New password' : 'Password'" :required="!editingUserId">
            <UInput v-model="userForm.password" type="password" autocomplete="new-password" />
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

        <div v-if="editingUserId" class="mt-6 rounded-xl border border-slate-200 bg-white p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <div>
              <h4 class="font-bold text-slate-950">Quick access controls</h4>
              <p class="text-sm text-slate-500">Use these for fast activation or suspension.</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <UButton
              v-for="option in quickStatusOptions"
              :key="option.value"
              :icon="option.icon"
              color="neutral"
              :variant="userForm.status === option.value ? 'solid' : 'outline'"
              :loading="isSaving && userForm.status === option.value"
              @click="setUserStatus(option.value as 'active' | 'suspended')"
            >
              {{ option.label }}
            </UButton>
          </div>
        </div>

        <div v-if="editingUserId" class="mt-6 rounded-xl border border-slate-200 bg-white p-4">
          <div class="mb-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h4 class="font-bold text-slate-950">Password reset support</h4>
              <p class="text-sm text-slate-500">Generate a reset token for the public password reset confirm flow.</p>
            </div>
            <UButton color="neutral" variant="outline" :loading="isSaving" @click="requestPasswordReset">
              <UIcon name="i-lucide-key-round" />
              Generate reset
            </UButton>
          </div>
          <div v-if="resetPayload" class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm">
            <p class="font-semibold text-blue-950">Reset payload for {{ resetPayload.email }}</p>
            <dl class="mt-2 grid grid-cols-1 gap-2 text-blue-900 md:grid-cols-2">
              <div>
                <dt class="font-semibold">UID</dt>
                <dd class="break-all font-mono text-xs">{{ resetPayload.uid }}</dd>
              </div>
              <div>
                <dt class="font-semibold">Token</dt>
                <dd class="break-all font-mono text-xs">{{ resetPayload.token }}</dd>
              </div>
              <div class="md:col-span-2">
                <dt class="font-semibold">Frontend path</dt>
                <dd class="break-all font-mono text-xs">{{ resetConfirmUrl() }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div v-if="editingUserId" class="mt-6 rounded-xl border border-slate-200 bg-white p-4">
          <div class="mb-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h4 class="font-bold text-slate-950">Product alerts</h4>
              <p class="text-sm text-slate-500">{{ activeAlertCount }} active alerts for this account.</p>
            </div>
            <UButton color="neutral" variant="outline" @click="loadUserProductAlerts()">
              <UIcon name="i-lucide-refresh-cw" />
              Refresh alerts
            </UButton>
          </div>

          <div v-if="!productAlerts.length" class="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">
            No product alerts recorded for this user.
          </div>
          <div v-else class="divide-y divide-slate-100 rounded-lg border border-slate-200">
            <div
              v-for="alert in productAlerts"
              :key="alert.id"
              class="flex flex-col gap-3 p-3 lg:flex-row lg:items-center lg:justify-between"
            >
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ alert.product_title || `Product #${alert.product_id}` }}</p>
                <p class="text-xs text-slate-500">{{ alert.email || userForm.email }} - {{ formatDate(alert.date_created) }}</p>
              </div>
              <div class="flex items-center gap-2">
                <UBadge :color="alert.status === 'Active' ? 'success' : alert.status === 'Unconfirmed' ? 'warning' : 'neutral'" variant="soft">
                  {{ alert.status }}
                </UBadge>
                <UButton
                  v-if="alert.status === 'Active' || alert.status === 'Unconfirmed'"
                  color="error"
                  variant="ghost"
                  size="sm"
                  @click="cancelAlert(alert)"
                >
                  Cancel
                </UButton>
              </div>
            </div>
          </div>
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
