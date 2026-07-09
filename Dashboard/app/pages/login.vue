<script setup lang="ts">
definePageMeta({
  layout: false,
})

const auth = useAuth()
const toast = useToast()
const form = reactive({
  identifier: '',
  password: '',
})

const canSubmit = computed(() => form.identifier.trim().length > 0 && form.password.length > 0 && !auth.isLoading.value)

async function submit() {
  if (!canSubmit.value)
    return

  const result = await auth.login({
    identifier: form.identifier.trim(),
    password: form.password,
  })

  if (result.success) {
    toast.add({
      title: 'Welcome back',
      description: 'Dashboard session is ready.',
      color: 'success',
    })
    await navigateTo('/')
    return
  }

  toast.add({
    title: 'Could not sign in',
    description: result.error || 'Check your email and password.',
    color: 'error',
  })
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-[#f4f7fb] px-4 py-10">
    <section class="grid w-full max-w-5xl overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-xl md:grid-cols-[1fr_0.9fr]">
      <div class="hidden min-h-[620px] flex-col justify-between bg-[#0f172a] p-10 text-white md:flex">
        <div>
          <div class="mb-10 flex items-center gap-3">
            <div class="flex h-12 w-16 items-center justify-center overflow-hidden rounded-xl bg-white">
              <img src="/brand/reesolmart-logo.jpg" alt="" class="h-full w-full object-contain">
            </div>
            <div>
              <p class="text-xl font-bold leading-tight">
                Reesolmart
              </p>
              <p class="text-sm text-slate-300">
                Just in time, buying
              </p>
            </div>
          </div>

          <h1 class="max-w-md text-4xl font-black leading-tight">
            Manage products, orders, customers, and store operations from one place.
          </h1>
          <p class="mt-5 max-w-md text-base leading-7 text-slate-300">
            Changes made here flow through the backend and become visible in the customer storefront where supported by the existing APIs.
          </p>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-2xl font-black">
              01
            </p>
            <p class="mt-1 text-xs text-slate-300">
              Products
            </p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-2xl font-black">
              02
            </p>
            <p class="mt-1 text-xs text-slate-300">
              Orders
            </p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-2xl font-black">
              03
            </p>
            <p class="mt-1 text-xs text-slate-300">
              Customers
            </p>
          </div>
        </div>
      </div>

      <form class="p-6 sm:p-10 md:p-12" @submit.prevent="submit">
        <div class="mb-9 flex items-center gap-3 md:hidden">
          <div class="flex h-12 w-16 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white">
            <img src="/brand/reesolmart-logo.jpg" alt="" class="h-full w-full object-contain">
          </div>
          <div>
            <p class="text-xl font-bold leading-tight text-slate-950">
              Reesolmart
            </p>
            <p class="text-sm text-slate-500">
              Just in time, buying
            </p>
          </div>
        </div>

        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-[#30328f]">
            Secure access
          </p>
          <h2 class="mt-3 text-3xl font-black tracking-tight text-slate-950">
            Sign in
          </h2>
          <p class="mt-3 text-sm leading-6 text-slate-500">
            Use a staff account with dashboard permissions.
          </p>
        </div>

        <div class="mt-8 space-y-5">
          <UFormField label="Email or username">
            <UInput
              v-model="form.identifier"
              size="xl"
              icon="i-lucide-user"
              autocomplete="username"
              placeholder="admin@example.com"
            />
          </UFormField>

          <UFormField label="Password">
            <PasswordInput
              v-model="form.password"
              size="xl"
              icon="i-lucide-lock"
              autocomplete="current-password"
              placeholder="Enter password"
            />
          </UFormField>

          <UAlert
            v-if="auth.error.value"
            color="neutral"
            variant="soft"
            icon="i-lucide-info"
            :description="auth.error.value"
          />

          <UButton
            type="submit"
            size="xl"
            block
            color="primary"
            icon="i-lucide-log-in"
            :loading="auth.isLoading.value"
            :disabled="!canSubmit"
          >
            Sign in to dashboard
          </UButton>
        </div>
      </form>
    </section>
  </main>
</template>
