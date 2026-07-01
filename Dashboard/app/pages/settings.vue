<script setup lang="ts">
const colorMode = useColorMode();
const toast = useToast();
const { getSettings, updateSettings } = useSettings();
const { getEmailConfig, updateEmailConfig, sendTestEmail } = useEmailConfig();
const { getPaymentConfig, updatePaymentConfig } = usePaymentConfig();

const theme = ref(colorMode.preference);
const isLoading = ref(false);
const isSaving = ref(false);
const isEmailLoading = ref(false);
const isEmailSaving = ref(false);
const isEmailTesting = ref(false);
const isPaymentLoading = ref(false);
const isPaymentSaving = ref(false);
const themeOptions = [
  { label: "Light", value: "light", icon: "i-lucide-sun" },
  { label: "Dark", value: "dark", icon: "i-lucide-moon" },
  { label: "System", value: "system", icon: "i-lucide-monitor" },
];

const store = ref({
  site_name: "",
  site_domain: "",
  default_currency: "",
  shop_name: "",
  support_email: "",
  reply_to_email: "",
  payment_methods: [] as Array<{ code: string; name: string; type: string; requires_prepayment: boolean; is_configured?: boolean }>,
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

const emailConfig = ref({
  is_enabled: false,
  is_configured: false,
  host: "",
  port: 587,
  username: "",
  password: "",
  has_password: false,
  use_tls: true,
  use_ssl: false,
  timeout_seconds: 30,
  from_email: "",
  reply_to_email: "",
  sales_recipients: "",
});
const testEmailRecipient = ref("");

const paymentConfig = ref({
  mpesa: {
    is_enabled: true,
    is_configured: false,
    checkout_visible: false,
    missing_requirements: [] as string[],
    base_url: "https://sandbox.safaricom.co.ke",
    consumer_key: "",
    has_consumer_key: false,
    consumer_secret: "",
    has_consumer_secret: false,
    shortcode: "",
    passkey: "",
    has_passkey: false,
    callback_url: "",
    transaction_type: "CustomerPayBillOnline",
    timeout_seconds: 30,
  },
  pesapal: {
    is_enabled: true,
    is_configured: false,
    checkout_visible: false,
    missing_requirements: [] as string[],
    base_url: "https://cybqa.pesapal.com/pesapalv3/api",
    consumer_key: "",
    has_consumer_key: false,
    consumer_secret: "",
    has_consumer_secret: false,
    callback_url: "",
    cancellation_url: "",
    ipn_url: "",
    ipn_id: "",
    notification_type: "POST",
    branch: "",
    redirect_mode: "TOP_WINDOW",
    timeout_seconds: 30,
  },
  airtel_money: {
    is_enabled: true,
    is_configured: false,
    checkout_visible: false,
    missing_requirements: [] as string[],
    provider_name: "sandbox_airtel_money",
    sandbox_enabled: false,
  },
  card: {
    is_enabled: true,
    is_configured: false,
    checkout_visible: false,
    missing_requirements: [] as string[],
    provider_name: "sandbox_card",
    sandbox_enabled: false,
  },
});

function paymentVisibilityBadge(provider: keyof typeof paymentConfig.value) {
  const config = paymentConfig.value[provider];
  if (config.checkout_visible)
    return { color: "success" as const, label: "Visible at checkout" };
  if (!config.is_enabled)
    return { color: "neutral" as const, label: "Disabled" };
  return { color: "warning" as const, label: "Hidden at checkout" };
}

function paymentMissingText(provider: keyof typeof paymentConfig.value) {
  const missing = paymentConfig.value[provider].missing_requirements || [];
  if (!missing.length)
    return "";
  return `Missing: ${missing.map((item) => item.replaceAll("_", " ")).join(", ")}.`;
}

function useMpesaSandboxPreset() {
  paymentConfig.value.mpesa.base_url = "https://sandbox.safaricom.co.ke";
  paymentConfig.value.mpesa.transaction_type = paymentConfig.value.mpesa.transaction_type || "CustomerPayBillOnline";
}

function useMpesaLivePreset() {
  paymentConfig.value.mpesa.base_url = "https://api.safaricom.co.ke";
  paymentConfig.value.mpesa.transaction_type = paymentConfig.value.mpesa.transaction_type || "CustomerPayBillOnline";
}

function usePesapalSandboxPreset() {
  paymentConfig.value.pesapal.base_url = "https://cybqa.pesapal.com/pesapalv3/api";
}

function usePesapalLivePreset() {
  paymentConfig.value.pesapal.base_url = "https://pay.pesapal.com/v3/api";
}

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

async function loadPaymentConfig() {
  isPaymentLoading.value = true;
  const result = await getPaymentConfig();
  if (result.success && result.data) {
    paymentConfig.value = {
      mpesa: {
        ...paymentConfig.value.mpesa,
        ...result.data.mpesa,
        consumer_key: "",
        consumer_secret: "",
        passkey: "",
      },
      pesapal: {
        ...paymentConfig.value.pesapal,
        ...result.data.pesapal,
        consumer_key: "",
        consumer_secret: "",
      },
      airtel_money: {
        ...paymentConfig.value.airtel_money,
        ...result.data.airtel_money,
      },
      card: {
        ...paymentConfig.value.card,
        ...result.data.card,
      },
    };
  }
  else {
    toast.add({
      title: "Could not load payment settings",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
  isPaymentLoading.value = false;
}

async function loadEmailConfig() {
  isEmailLoading.value = true;
  const result = await getEmailConfig();
  if (result.success && result.data) {
    emailConfig.value = {
      ...emailConfig.value,
      ...result.data,
      password: "",
    };
    testEmailRecipient.value = profile.value.email || result.data.from_email || "";
  }
  else {
    toast.add({
      title: "Could not load email settings",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
  isEmailLoading.value = false;
}

function changeTheme(value: string) {
  if (!["light", "dark", "system"].includes(value))
    return;
  theme.value = value;
  colorMode.preference = value;
}

watch(
  () => colorMode.preference,
  (value) => {
    if (["light", "dark", "system"].includes(value))
      theme.value = value;
  },
);

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

async function savePaymentConfig() {
  isPaymentSaving.value = true;
  const mpesaPayload: Record<string, any> = {
    is_enabled: paymentConfig.value.mpesa.is_enabled,
    base_url: paymentConfig.value.mpesa.base_url,
    shortcode: paymentConfig.value.mpesa.shortcode,
    callback_url: paymentConfig.value.mpesa.callback_url,
    transaction_type: paymentConfig.value.mpesa.transaction_type,
    timeout_seconds: Number(paymentConfig.value.mpesa.timeout_seconds || 30),
  };

  if (paymentConfig.value.mpesa.consumer_key)
    mpesaPayload.consumer_key = paymentConfig.value.mpesa.consumer_key;
  if (paymentConfig.value.mpesa.consumer_secret)
    mpesaPayload.consumer_secret = paymentConfig.value.mpesa.consumer_secret;
  if (paymentConfig.value.mpesa.passkey)
    mpesaPayload.passkey = paymentConfig.value.mpesa.passkey;

  const pesapalPayload: Record<string, any> = {
    is_enabled: paymentConfig.value.pesapal.is_enabled,
    base_url: paymentConfig.value.pesapal.base_url,
    callback_url: paymentConfig.value.pesapal.callback_url,
    cancellation_url: paymentConfig.value.pesapal.cancellation_url,
    ipn_url: paymentConfig.value.pesapal.ipn_url,
    ipn_id: paymentConfig.value.pesapal.ipn_id,
    notification_type: paymentConfig.value.pesapal.notification_type || "POST",
    branch: paymentConfig.value.pesapal.branch,
    redirect_mode: paymentConfig.value.pesapal.redirect_mode || "TOP_WINDOW",
    timeout_seconds: Number(paymentConfig.value.pesapal.timeout_seconds || 30),
  };

  if (paymentConfig.value.pesapal.consumer_key)
    pesapalPayload.consumer_key = paymentConfig.value.pesapal.consumer_key;
  if (paymentConfig.value.pesapal.consumer_secret)
    pesapalPayload.consumer_secret = paymentConfig.value.pesapal.consumer_secret;

  const result = await updatePaymentConfig({
    mpesa: mpesaPayload,
    pesapal: pesapalPayload,
    airtel_money: {
      is_enabled: paymentConfig.value.airtel_money.is_enabled,
      provider_name: paymentConfig.value.airtel_money.provider_name,
    },
    card: {
      is_enabled: paymentConfig.value.card.is_enabled,
      provider_name: paymentConfig.value.card.provider_name,
    },
  });

  if (result.success && result.data) {
    paymentConfig.value = {
      mpesa: {
        ...paymentConfig.value.mpesa,
        ...result.data.mpesa,
        consumer_key: "",
        consumer_secret: "",
        passkey: "",
      },
      pesapal: {
        ...paymentConfig.value.pesapal,
        ...result.data.pesapal,
        consumer_key: "",
        consumer_secret: "",
      },
      airtel_money: {
        ...paymentConfig.value.airtel_money,
        ...result.data.airtel_money,
      },
      card: {
        ...paymentConfig.value.card,
        ...result.data.card,
      },
    };
    toast.add({
      title: "Payment integrations saved",
      description: "Checkout will use the updated provider configuration.",
      color: "success",
    });
  }
  else {
    toast.add({
      title: "Could not save payment integrations",
      description: result.error || "Please check the form and try again.",
      color: "error",
    });
  }

  isPaymentSaving.value = false;
}

function setEmailSecurityMode(mode: "tls" | "ssl" | "none") {
  emailConfig.value.use_tls = mode === "tls";
  emailConfig.value.use_ssl = mode === "ssl";

  if (mode === "tls" && Number(emailConfig.value.port || 0) === 465)
    emailConfig.value.port = 587;
  if (mode === "ssl" && Number(emailConfig.value.port || 0) === 587)
    emailConfig.value.port = 465;
}

function applyGmailSmtpPreset() {
  emailConfig.value = {
    ...emailConfig.value,
    is_enabled: true,
    host: "smtp.gmail.com",
    port: 587,
    use_tls: true,
    use_ssl: false,
  };

  if (!emailConfig.value.from_email && emailConfig.value.username)
    emailConfig.value.from_email = emailConfig.value.username;
  if (!emailConfig.value.reply_to_email && emailConfig.value.username)
    emailConfig.value.reply_to_email = emailConfig.value.username;
}

async function saveEmailConfig() {
  isEmailSaving.value = true;
  const payload: Record<string, any> = {
    is_enabled: emailConfig.value.is_enabled,
    host: emailConfig.value.host,
    port: Number(emailConfig.value.port || 587),
    username: emailConfig.value.username,
    use_tls: emailConfig.value.use_tls,
    use_ssl: emailConfig.value.use_ssl,
    timeout_seconds: Number(emailConfig.value.timeout_seconds || 30),
    from_email: emailConfig.value.from_email,
    reply_to_email: emailConfig.value.reply_to_email,
    sales_recipients: emailConfig.value.sales_recipients,
  };
  if (emailConfig.value.password)
    payload.password = emailConfig.value.password;

  const result = await updateEmailConfig({ email: payload });
  if (result.success && result.data) {
    emailConfig.value = {
      ...emailConfig.value,
      ...result.data,
      password: "",
    };
    toast.add({
      title: "Email settings saved",
      description: "Notification emails will use the updated deliverability settings.",
      color: "success",
    });
  }
  else {
    toast.add({
      title: "Could not save email settings",
      description: result.error || "Please check the form and try again.",
      color: "error",
    });
  }
  isEmailSaving.value = false;
}

async function runTestEmail() {
  isEmailTesting.value = true;
  const result = await sendTestEmail(testEmailRecipient.value);
  toast.add({
    title: result.success ? "Test email sent" : "Test email failed",
    description: result.success ? result.data?.detail || "The backend accepted the test email." : result.error || "Please check the SMTP configuration.",
    color: result.success ? "success" : "error",
  });
  isEmailTesting.value = false;
}

onMounted(() => {
  void loadSettings();
  void loadEmailConfig();
  void loadPaymentConfig();
});
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
            <UInput v-model="store.site_name" :loading="isLoading" placeholder="Reesolmart" />
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
          <div class="grid grid-cols-3 overflow-hidden rounded-md border border-default">
            <UButton
              v-for="option in themeOptions"
              :key="option.value"
              :icon="option.icon"
              color="neutral"
              :variant="theme === option.value ? 'solid' : 'ghost'"
              class="justify-center rounded-none"
              @click="changeTheme(option.value)"
            >
              {{ option.label }}
            </UButton>
          </div>
          <p class="text-xs text-(--ui-text-muted)">Current mode: {{ colorMode.value === 'dark' ? 'Dark' : 'Light' }}</p>
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
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 class="text-lg font-semibold">Email Deliverability</h3>
              <p class="text-sm text-(--ui-text-muted)">Configure outbound SMTP for account, password, order, and notification emails.</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <UBadge :color="emailConfig.is_configured ? 'success' : 'warning'" variant="soft">
                {{ emailConfig.is_configured ? "Configured" : "Incomplete" }}
              </UBadge>
              <UButton color="neutral" variant="outline" icon="i-lucide-mail" @click="applyGmailSmtpPreset">
                Use Gmail SMTP
              </UButton>
              <UButton color="primary" icon="i-lucide-save" :loading="isEmailSaving" @click="saveEmailConfig">
                Save Email Settings
              </UButton>
            </div>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="md:col-span-2">
              <UCheckbox v-model="emailConfig.is_enabled" label="Enable SMTP delivery" :disabled="isEmailLoading" />
            </div>
            <UFormField label="SMTP host">
              <UInput v-model="emailConfig.host" :loading="isEmailLoading" placeholder="smtp.example.com" />
            </UFormField>
            <UFormField label="Port">
              <UInput v-model.number="emailConfig.port" :loading="isEmailLoading" type="number" min="1" max="65535" />
            </UFormField>
            <UFormField label="Username">
              <UInput v-model="emailConfig.username" :loading="isEmailLoading" autocomplete="username" placeholder="yourname@gmail.com" />
            </UFormField>
            <UFormField label="Password / API key">
              <UInput v-model="emailConfig.password" :loading="isEmailLoading" type="password" :placeholder="emailConfig.has_password ? 'Saved' : 'Google app password'" autocomplete="new-password" />
            </UFormField>
            <UFormField label="From email">
              <UInput v-model="emailConfig.from_email" :loading="isEmailLoading" type="email" placeholder="no-reply@example.com" />
            </UFormField>
            <UFormField label="Reply-to email">
              <UInput v-model="emailConfig.reply_to_email" :loading="isEmailLoading" type="email" placeholder="support@example.com" />
            </UFormField>
            <UFormField label="Security">
              <UButtonGroup class="w-full">
                <UButton :variant="emailConfig.use_tls ? 'solid' : 'subtle'" color="neutral" @click="setEmailSecurityMode('tls')">TLS</UButton>
                <UButton :variant="emailConfig.use_ssl ? 'solid' : 'subtle'" color="neutral" @click="setEmailSecurityMode('ssl')">SSL</UButton>
                <UButton :variant="!emailConfig.use_tls && !emailConfig.use_ssl ? 'solid' : 'subtle'" color="neutral" @click="setEmailSecurityMode('none')">None</UButton>
              </UButtonGroup>
            </UFormField>
            <UFormField label="Timeout seconds">
              <UInput v-model.number="emailConfig.timeout_seconds" :loading="isEmailLoading" type="number" min="1" max="120" />
            </UFormField>
            <UFormField class="md:col-span-2" label="Sales recipients">
              <UInput v-model="emailConfig.sales_recipients" :loading="isEmailLoading" placeholder="sales@example.com, support@example.com" />
            </UFormField>
          </div>

          <div class="rounded-lg border border-default p-4">
            <h4 class="font-semibold">Test Delivery</h4>
            <p class="mt-1 text-xs text-(--ui-text-muted)">Sends a simple message using the current saved configuration.</p>
            <div class="mt-4 space-y-3">
              <UFormField label="Recipient">
                <UInput v-model="testEmailRecipient" type="email" placeholder="admin@example.com" />
              </UFormField>
              <UButton class="w-full justify-center" color="neutral" variant="outline" icon="i-lucide-send" :loading="isEmailTesting" :disabled="!testEmailRecipient" @click="runTestEmail">
                Send Test Email
              </UButton>
              <p class="text-xs text-(--ui-text-muted)">
                Save changes before testing if you changed host, credentials, or sender details.
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <UCard class="lg:col-span-3">
        <template #header>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 class="text-lg font-semibold">Payment Integrations</h3>
              <p class="text-sm text-(--ui-text-muted)">Provider details are stored on the backend and used during checkout.</p>
            </div>
            <UButton color="primary" icon="i-lucide-save" :loading="isPaymentSaving" @click="savePaymentConfig">
              Save Payment Settings
            </UButton>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <div class="rounded-lg border border-default p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <h4 class="font-semibold">M-Pesa Daraja</h4>
                <p class="text-xs text-(--ui-text-muted)">STK push and callback configuration.</p>
              </div>
              <UBadge :color="paymentVisibilityBadge('mpesa').color" variant="soft">
                {{ paymentVisibilityBadge('mpesa').label }}
              </UBadge>
            </div>

            <div class="space-y-4">
              <UCheckbox v-model="paymentConfig.mpesa.is_enabled" label="Enable M-Pesa at checkout" :disabled="isPaymentLoading" />
              <div class="grid grid-cols-2 gap-2">
                <UButton color="neutral" variant="outline" block size="sm" @click="useMpesaSandboxPreset">
                  Sandbox URL
                </UButton>
                <UButton color="neutral" variant="outline" block size="sm" @click="useMpesaLivePreset">
                  Live URL
                </UButton>
              </div>
              <UFormField label="Base URL">
                <UInput v-model="paymentConfig.mpesa.base_url" :loading="isPaymentLoading" placeholder="https://sandbox.safaricom.co.ke" />
              </UFormField>
              <UFormField label="Consumer key">
                <UInput v-model="paymentConfig.mpesa.consumer_key" :loading="isPaymentLoading" type="password" :placeholder="paymentConfig.mpesa.has_consumer_key ? 'Saved' : 'Required'" autocomplete="new-password" />
              </UFormField>
              <UFormField label="Consumer secret">
                <UInput v-model="paymentConfig.mpesa.consumer_secret" :loading="isPaymentLoading" type="password" :placeholder="paymentConfig.mpesa.has_consumer_secret ? 'Saved' : 'Required'" autocomplete="new-password" />
              </UFormField>
              <UFormField label="Shortcode">
                <UInput v-model="paymentConfig.mpesa.shortcode" :loading="isPaymentLoading" placeholder="174379" />
              </UFormField>
              <UFormField label="Passkey">
                <UInput v-model="paymentConfig.mpesa.passkey" :loading="isPaymentLoading" type="password" :placeholder="paymentConfig.mpesa.has_passkey ? 'Saved' : 'Required'" autocomplete="new-password" />
              </UFormField>
              <UFormField label="Callback URL">
                <UInput v-model="paymentConfig.mpesa.callback_url" :loading="isPaymentLoading" placeholder="https://example.com/api/v1/payments/mpesa/callback/" />
              </UFormField>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <UFormField label="Transaction type">
                  <UInput v-model="paymentConfig.mpesa.transaction_type" :loading="isPaymentLoading" placeholder="CustomerPayBillOnline" />
                </UFormField>
                <UFormField label="Timeout seconds">
                  <UInput v-model.number="paymentConfig.mpesa.timeout_seconds" :loading="isPaymentLoading" type="number" min="1" max="120" />
                </UFormField>
              </div>
              <p class="text-xs text-(--ui-text-muted)">
                M-Pesa appears at checkout only when enabled and all Daraja credentials, shortcode, passkey, and callback URL are saved.
              </p>
              <p v-if="paymentMissingText('mpesa')" class="text-xs text-warning">
                {{ paymentMissingText('mpesa') }}
              </p>
            </div>
          </div>

          <div class="rounded-lg border border-default p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <h4 class="font-semibold">Pesapal</h4>
                <p class="text-xs text-(--ui-text-muted)">Hosted checkout, callback, and IPN configuration.</p>
              </div>
              <UBadge :color="paymentVisibilityBadge('pesapal').color" variant="soft">
                {{ paymentVisibilityBadge('pesapal').label }}
              </UBadge>
            </div>

            <div class="space-y-4">
              <UCheckbox v-model="paymentConfig.pesapal.is_enabled" label="Enable Pesapal at checkout" :disabled="isPaymentLoading" />
              <div class="grid grid-cols-2 gap-2">
                <UButton color="neutral" variant="outline" block size="sm" @click="usePesapalSandboxPreset">
                  Sandbox URL
                </UButton>
                <UButton color="neutral" variant="outline" block size="sm" @click="usePesapalLivePreset">
                  Live URL
                </UButton>
              </div>
              <UFormField label="Base URL">
                <UInput v-model="paymentConfig.pesapal.base_url" :loading="isPaymentLoading" placeholder="https://cybqa.pesapal.com/pesapalv3/api" />
              </UFormField>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <UFormField label="Consumer key">
                  <UInput v-model="paymentConfig.pesapal.consumer_key" :loading="isPaymentLoading" type="password" :placeholder="paymentConfig.pesapal.has_consumer_key ? 'Saved' : 'Required'" autocomplete="new-password" />
                </UFormField>
                <UFormField label="Consumer secret">
                  <UInput v-model="paymentConfig.pesapal.consumer_secret" :loading="isPaymentLoading" type="password" :placeholder="paymentConfig.pesapal.has_consumer_secret ? 'Saved' : 'Required'" autocomplete="new-password" />
                </UFormField>
              </div>
              <UFormField label="Checkout callback URL">
                <UInput v-model="paymentConfig.pesapal.callback_url" :loading="isPaymentLoading" placeholder="https://store.example.com/checkout/review" />
              </UFormField>
              <UFormField label="Cancellation URL">
                <UInput v-model="paymentConfig.pesapal.cancellation_url" :loading="isPaymentLoading" placeholder="https://store.example.com/checkout/payment" />
              </UFormField>
              <UFormField label="IPN URL">
                <UInput v-model="paymentConfig.pesapal.ipn_url" :loading="isPaymentLoading" placeholder="https://api.example.com/api/v1/payments/pesapal/ipn/" />
              </UFormField>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <UFormField label="IPN ID">
                  <UInput v-model="paymentConfig.pesapal.ipn_id" :loading="isPaymentLoading" placeholder="Registered Pesapal notification ID" />
                </UFormField>
                <UFormField label="Notification type">
                  <USelect v-model="paymentConfig.pesapal.notification_type" :items="['POST', 'GET']" :loading="isPaymentLoading" />
                </UFormField>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <UFormField label="Branch">
                  <UInput v-model="paymentConfig.pesapal.branch" :loading="isPaymentLoading" placeholder="Optional" />
                </UFormField>
                <UFormField label="Redirect mode">
                  <UInput v-model="paymentConfig.pesapal.redirect_mode" :loading="isPaymentLoading" placeholder="TOP_WINDOW" />
                </UFormField>
                <UFormField label="Timeout seconds">
                  <UInput v-model.number="paymentConfig.pesapal.timeout_seconds" :loading="isPaymentLoading" type="number" min="1" max="120" />
                </UFormField>
              </div>
              <p class="text-xs text-(--ui-text-muted)">
                Pesapal appears at checkout only when enabled and consumer credentials, callback URL, and IPN ID are saved.
              </p>
              <p v-if="paymentMissingText('pesapal')" class="text-xs text-warning">
                {{ paymentMissingText('pesapal') }}
              </p>
            </div>
          </div>

          <div class="rounded-lg border border-default p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <h4 class="font-semibold">Airtel Money</h4>
                <p class="text-xs text-(--ui-text-muted)">Mobile collection provider controls.</p>
              </div>
              <UBadge :color="paymentVisibilityBadge('airtel_money').color" variant="soft">
                {{ paymentVisibilityBadge('airtel_money').label }}
              </UBadge>
            </div>

            <div class="space-y-4">
              <UCheckbox v-model="paymentConfig.airtel_money.is_enabled" label="Enable Airtel Money at checkout" :disabled="isPaymentLoading || !paymentConfig.airtel_money.sandbox_enabled" />
              <UFormField label="Provider name">
                <UInput v-model="paymentConfig.airtel_money.provider_name" :loading="isPaymentLoading" placeholder="sandbox_airtel_money" />
              </UFormField>
              <p class="text-xs text-(--ui-text-muted)">
                Backend sandbox flag: {{ paymentConfig.airtel_money.sandbox_enabled ? "Enabled" : "Disabled" }}. This provider remains hidden from checkout unless its backend integration is enabled.
              </p>
              <p v-if="paymentMissingText('airtel_money')" class="text-xs text-warning">
                {{ paymentMissingText('airtel_money') }}
              </p>
            </div>
          </div>

          <div class="rounded-lg border border-default p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <h4 class="font-semibold">Cards</h4>
                <p class="text-xs text-(--ui-text-muted)">Sandbox card authorization controls.</p>
              </div>
              <UBadge :color="paymentVisibilityBadge('card').color" variant="soft">
                {{ paymentVisibilityBadge('card').label }}
              </UBadge>
            </div>

            <div class="space-y-4">
              <UCheckbox v-model="paymentConfig.card.is_enabled" label="Enable cards at checkout" :disabled="isPaymentLoading || !paymentConfig.card.sandbox_enabled" />
              <UFormField label="Provider name">
                <UInput v-model="paymentConfig.card.provider_name" :loading="isPaymentLoading" placeholder="sandbox_card" />
              </UFormField>
              <p class="text-xs text-(--ui-text-muted)">
                Backend sandbox flag: {{ paymentConfig.card.sandbox_enabled ? "Enabled" : "Disabled" }}. Real card payments require adding a PCI/tokenization provider before enabling this in production.
              </p>
              <p v-if="paymentMissingText('card')" class="text-xs text-warning">
                {{ paymentMissingText('card') }}
              </p>
            </div>
          </div>
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
