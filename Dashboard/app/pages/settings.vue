<script setup lang="ts">
const colorMode = useColorMode();
const toast = useToast();
const { getSettings, updateSettings } = useSettings();

const theme = ref(colorMode.preference);
const isLoading = ref(false);
const isSaving = ref(false);

const store = ref({
  site_name: "",
  site_domain: "",
  default_currency: "",
  shop_name: "",
  support_email: "",
  reply_to_email: "",
  payment_methods: [] as Array<{ code: string; name: string; type: string; requires_prepayment: boolean }>,
  async_enabled: false,
  search_host: "",
});

const profile = ref({
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  company: "",
  country_code: "",
  preferred_currency: "",
  receive_order_updates: true,
  receive_marketing_emails: false,
});

function applySettings(data: any) {
  store.value = {
    ...store.value,
    ...(data.store || {}),
  };
  const user = data.profile || {};
  profile.value = {
    email: user.email || "",
    first_name: user.first_name || "",
    last_name: user.last_name || "",
    phone: user.phone || "",
    company: user.company || "",
    country_code: user.country_code || "",
    preferred_currency: user.preferred_currency || "",
    receive_order_updates: Boolean(user.settings?.receive_order_updates),
    receive_marketing_emails: Boolean(user.settings?.receive_marketing_emails),
  };
}

async function loadSettings() {
  isLoading.value = true;
  const result = await getSettings();
  if (result.success)
    applySettings(result.data);
  else
    toast.add({
      title: "Could not load settings",
      description: result.error || "Please try again.",
      color: "error",
    });
  isLoading.value = false;
}

function changeTheme(value: string) {
  if (!["light", "dark", "system"].includes(value))
    return;
  theme.value = value;
  colorMode.preference = value;
}

async function saveSettings() {
  isSaving.value = true;
  const result = await updateSettings({
    store: {
      site_name: store.value.site_name,
      site_domain: store.value.site_domain,
    },
    profile: {
      email: profile.value.email,
      first_name: profile.value.first_name,
      last_name: profile.value.last_name,
      phone: profile.value.phone,
      company: profile.value.company,
      country_code: profile.value.country_code,
      preferred_currency: profile.value.preferred_currency,
      receive_order_updates: profile.value.receive_order_updates,
      receive_marketing_emails: profile.value.receive_marketing_emails,
    },
  });

  if (result.success) {
    applySettings(result.data);
    toast.add({
      title: "Settings saved",
      description: "Dashboard settings were updated successfully.",
      color: "success",
    });
  }
  else {
    toast.add({
      title: "Could not save settings",
      description: result.error || "Please check the form and try again.",
      color: "error",
    });
  }
  isSaving.value = false;
}

onMounted(loadSettings);
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col px-6 py-6">
    <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="text-2xl font-bold">Settings</h2>
        <p class="text-sm text-(--ui-text-muted)">Manage store identity, admin profile, and runtime visibility.</p>
      </div>
      <UButton color="primary" icon="i-lucide-save" :loading="isSaving" @click="saveSettings">
        Save Settings
      </UButton>
    </div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <UCard class="lg:col-span-2">
        <template #header>
          <div>
            <h3 class="text-lg font-semibold">Store Identity</h3>
            <p class="text-sm text-(--ui-text-muted)">Editable values are persisted in Django Sites.</p>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <UFormField label="Site Name" required>
            <UInput v-model="store.site_name" :loading="isLoading" placeholder="Vortexus" />
          </UFormField>
          <UFormField label="Site Domain" required>
            <UInput v-model="store.site_domain" :loading="isLoading" placeholder="admin.example.com" />
          </UFormField>
          <UFormField label="Shop Name">
            <UInput v-model="store.shop_name" disabled />
          </UFormField>
          <UFormField label="Default Currency">
            <UInput v-model="store.default_currency" disabled />
          </UFormField>
          <UFormField label="Support Email">
            <UInput v-model="store.support_email" disabled />
          </UFormField>
          <UFormField label="Reply-To Email">
            <UInput v-model="store.reply_to_email" disabled />
          </UFormField>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-lg font-semibold">Appearance</h3>
            <p class="text-sm text-(--ui-text-muted)">Stored locally in this dashboard.</p>
          </div>
        </template>

        <div class="space-y-4">
          <UButtonGroup class="w-full">
            <UButton icon="i-lucide-sun" color="neutral" :variant="theme === 'light' ? 'solid' : 'subtle'" @click="changeTheme('light')">
              Light
            </UButton>
            <UButton icon="i-lucide-moon" color="neutral" :variant="theme === 'dark' ? 'solid' : 'subtle'" @click="changeTheme('dark')">
              Dark
            </UButton>
            <UButton icon="i-lucide-computer" color="neutral" :variant="theme === 'system' ? 'solid' : 'subtle'" @click="changeTheme('system')">
              System
            </UButton>
          </UButtonGroup>
          <p class="text-xs text-(--ui-text-muted)">Theme is frontend-only for now; backend settings remain operational.</p>
        </div>
      </UCard>

      <UCard class="lg:col-span-2">
        <template #header>
          <div>
            <h3 class="text-lg font-semibold">Admin Profile</h3>
            <p class="text-sm text-(--ui-text-muted)">Updates the currently logged-in admin account.</p>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <UFormField label="First Name">
            <UInput v-model="profile.first_name" :loading="isLoading" />
          </UFormField>
          <UFormField label="Last Name">
            <UInput v-model="profile.last_name" :loading="isLoading" />
          </UFormField>
          <UFormField label="Email" required>
            <UInput v-model="profile.email" type="email" :loading="isLoading" />
          </UFormField>
          <UFormField label="Phone">
            <UInput v-model="profile.phone" :loading="isLoading" />
          </UFormField>
          <UFormField label="Company">
            <UInput v-model="profile.company" :loading="isLoading" />
          </UFormField>
          <UFormField label="Country Code">
            <UInput v-model="profile.country_code" maxlength="2" placeholder="KE" :loading="isLoading" />
          </UFormField>
          <UFormField label="Preferred Currency">
            <UInput v-model="profile.preferred_currency" maxlength="3" placeholder="KES" :loading="isLoading" />
          </UFormField>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-lg font-semibold">Notifications</h3>
            <p class="text-sm text-(--ui-text-muted)">Stored on the admin profile.</p>
          </div>
        </template>

        <div class="space-y-4">
          <UCheckbox v-model="profile.receive_order_updates" label="Receive order updates" />
          <UCheckbox v-model="profile.receive_marketing_emails" label="Receive marketing emails" />
        </div>
      </UCard>

      <UCard class="lg:col-span-3">
        <template #header>
          <div>
            <h3 class="text-lg font-semibold">Runtime Configuration</h3>
            <p class="text-sm text-(--ui-text-muted)">Read-only operational values exposed without secrets.</p>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div class="rounded-lg border border-default p-4">
            <div class="text-xs uppercase tracking-wide text-(--ui-text-muted)">Async Tasks</div>
            <div class="mt-1 text-lg font-semibold">{{ store.async_enabled ? "Enabled" : "Disabled" }}</div>
          </div>
          <div class="rounded-lg border border-default p-4">
            <div class="text-xs uppercase tracking-wide text-(--ui-text-muted)">Search Host</div>
            <div class="mt-1 truncate text-lg font-semibold">{{ store.search_host || "Not configured" }}</div>
          </div>
          <div class="rounded-lg border border-default p-4">
            <div class="text-xs uppercase tracking-wide text-(--ui-text-muted)">Payment Methods</div>
            <div class="mt-1 text-lg font-semibold">{{ store.payment_methods.length }}</div>
          </div>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <UBadge
            v-for="method in store.payment_methods"
            :key="method.code"
            color="neutral"
            variant="soft"
          >
            {{ method.name || method.code }}
          </UBadge>
        </div>
      </UCard>
    </div>
  </div>
</template>
