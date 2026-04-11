<script setup lang="ts">
const { fetchCurrentUser, isAuthenticated, loading, login } = useAdminAuth();
const toast = useToast();

const form = reactive({
  identifier: "admin@vortexus.demo",
  password: "",
});

const isSubmitting = ref(false);

onMounted(async () => {
  if (!isAuthenticated.value)
    await fetchCurrentUser();
  if (isAuthenticated.value)
    await navigateTo("/");
});

async function submitLogin() {
  isSubmitting.value = true;
  const result = await login(form.identifier, form.password);
  if (result.success) {
    toast.add({
      title: "Logged in",
      description: "Dashboard session is ready.",
      color: "success",
    });
    await navigateTo("/");
  }
  else {
    toast.add({
      title: "Login failed",
      description: result.error || "Check your credentials and try again.",
      color: "error",
    });
  }
  isSubmitting.value = false;
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-elevated px-4">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="space-y-1">
          <h1 class="text-2xl font-bold">Vortexus Admin</h1>
          <p class="text-sm text-(--ui-text-muted)">Sign in with a staff account to load live backend data.</p>
        </div>
      </template>

      <form class="space-y-4" @submit.prevent="submitLogin">
        <UFormField label="Email or username" required>
          <UInput
            v-model="form.identifier"
            autocomplete="username"
            icon="i-lucide-user"
            placeholder="admin@vortexus.demo"
          />
        </UFormField>

        <UFormField label="Password" required>
          <UInput
            v-model="form.password"
            autocomplete="current-password"
            icon="i-lucide-lock"
            placeholder="Enter password"
            type="password"
          />
        </UFormField>

        <UButton
          block
          color="primary"
          type="submit"
          :loading="isSubmitting || loading"
        >
          Sign In
        </UButton>
      </form>

      <template #footer>
        <p class="text-xs text-(--ui-text-muted)">
          Demo admin: <span class="font-medium">admin@vortexus.demo</span>
        </p>
      </template>
    </UCard>
  </div>
</template>
