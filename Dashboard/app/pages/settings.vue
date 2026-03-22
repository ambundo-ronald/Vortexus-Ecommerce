<script setup lang="ts">
const colorMode = useColorMode();
const theme = ref(colorMode.preference);

const searchQuery = ref();

const notifications = ref({
  email: true,
  push: false,
});

const userInfo = ref({
  name: "",
  email: "user@example.com",
  twoFactorEnabled: false,
});

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validateName = (name: string): boolean => {
  return name.trim().length >= 2;
};

const saveUserInfo = async () => {
  try {
    if (!validateName(userInfo.value.name)) {
      throw new Error("Name must be at least 2 characters long");
    }
    if (!validateEmail(userInfo.value.email)) {
      throw new Error("Please enter a valid email address");
    }

    // Placeholder for API call
    // await $fetch('/api/user', { method: 'PUT', body: userInfo.value });

    const toast = useToast();
    toast.add({
      title: "Success",
      description: "Settings saved successfully",
      color: "success",
    });
  } catch (error) {
    const toast = useToast();
    toast.add({
      title: "Validation Error",
      description: error instanceof Error ? error.message : "Invalid input",
      color: "error",
    });
  }
};

const privacySettings = ref({
  analyticsConsent: true,
});

const changeTheme = (value: string) => {
  try {
    if (!["light", "dark", "system"].includes(value)) {
      throw new Error("Invalid theme value");
    }
    colorMode.preference = value;
  } catch (error) {
    const toast = useToast();
    toast.add({
      title: "Settings Error",
      description: "Failed to change theme",
      color: "error",
    });
  }
};
</script>

<template>
  <div
    class="max-w-3xl mx-auto w-full flex flex-col justify-center items-center px-8 py-4"
  >
    <div class="flex flex-col items-center justify-center mb-4">
      <h2 class="text-2xl font-bold">Settings</h2>
      <p class="text-(--ui-text-muted)">Manage your settings</p>
    </div>
    <UCard class="mb-4 w-full">
      <h3 class="font-medium text-lg mb-4">General</h3>
      <div class="space-y-6 max-w-6xl">
        <div class="flex items-center gap-8">
          <div class="w-1/2 pt-2">
            <div class="font-medium">Theme</div>
            <p class="text-(--ui-text-muted) text-sm">
              Customize your workspace
            </p>
          </div>
          <div class="flex-1">
            <UButtonGroup v-model="theme" class="w-full sm:w-auto">
              <UButton
                value="light"
                color="neutral"
                variant="subtle"
                @click="changeTheme('light')"
                icon="i-lucide-sun"
              >
                Light
              </UButton>
              <UButton
                value="dark"
                color="neutral"
                variant="subtle"
                @click="changeTheme('dark')"
                icon="i-lucide-moon"
              >
                Dark
              </UButton>
              <UButton
                value="system"
                color="neutral"
                variant="subtle"
                @click="changeTheme('system')"
                icon="i-lucide-computer"
              >
                System
              </UButton>
            </UButtonGroup>
          </div>
        </div>

        <div class="flex items-center gap-8">
          <div class="w-1/2 pt-2">
            <div class="font-medium">Language</div>
            <p class="text-(--ui-text-muted) text-sm">
              Set your preferred language
            </p>
          </div>
          <div class="flex-1">
            <USelect
              :items="[
                { label: 'English', value: 'en' },
                { label: 'Spanish', value: 'es' },
                { label: 'French', value: 'fr' },
                { label: 'German', value: 'de' },
              ]"
              value="en"
              placeholder="Select a language"
              class="w-full sm:w-64"
            />
          </div>
        </div>

        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2">
            <div class="font-medium">Notifications</div>
            <p class="text-(--ui-text-muted) text-sm">
              Enable/disable notifications
            </p>
          </div>
          <div class="flex-1 space-y-3">
            <UCheckbox
              v-model="notifications.email"
              label="Email Notifications"
            />
            <UCheckbox
              v-model="notifications.push"
              label="Push Notifications"
            />
          </div>
        </div>
      </div>

      <USeparator class="my-6" />

      <h3 class="font-medium text-lg mb-4">Account Settings</h3>

      <div class="space-y-6 max-w-6xl">
        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Name</div>
          <div class="flex-1">
            <UFormField class="mb-0">
              <UInput
                v-model="userInfo.name"
                placeholder="Your name"
                type="text"
                class="w-full sm:w-64"
              />
            </UFormField>
          </div>
        </div>

        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Email Address</div>
          <div class="flex-1">
            <UFormField class="mb-0">
              <UInput
                v-model="userInfo.email"
                placeholder="your@email.com"
                type="email"
                class="w-full sm:w-64"
              />
            </UFormField>
          </div>
        </div>

        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Password</div>
          <div class="flex-1">
            <UButton color="neutral" variant="subtle" size="sm"
              >Change Password</UButton
            >
          </div>
        </div>

        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Two-Factor Authentication</div>
          <div class="flex-1">
            <USwitch v-model="userInfo.twoFactorEnabled" />
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ userInfo.twoFactorEnabled ? "Enabled" : "Disabled" }}
            </div>
          </div>
        </div>
      </div>

      <USeparator class="my-6" />

      <h3 class="font-medium text-lg mb-4">Privacy & Data</h3>

      <div class="space-y-6 max-w-6xl">
        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Data Sharing</div>
          <div class="flex-1">
            <UCheckbox
              v-model="privacySettings.analyticsConsent"
              label="Share anonymous usage data"
            />
          </div>
        </div>

        <div class="flex items-start gap-8">
          <div class="w-1/2 pt-2 font-medium">Data Export</div>
          <div class="flex-1">
            <UButton color="neutral" variant="subtle" icon="i-lucide-download"
              >Export All Data</UButton
            >
          </div>
        </div>
      </div>

      <USeparator class="my-6" />

      <div class="flex justify-end">
        <UButton
          color="primary"
          size="sm"
          icon="i-lucide-save"
          @click="saveUserInfo"
        >
          Save Settings
        </UButton>
      </div>
    </UCard>
  </div>
</template>
