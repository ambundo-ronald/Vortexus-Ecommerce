// https://nuxt.com/docs/api/configuration/nuxt-config
const disableNuxtHub = process.env.DISABLE_NUXT_HUB === 'true' || process.env.NITRO_PRESET === 'node-server'

export default defineNuxtConfig({
  devtools: { enabled: false },
  ssr: process.env.NUXT_SSR !== 'false',

  modules: [
    '@nuxt/ui',
    '@nuxt/eslint',
    'nuxt-charts',
    ...(!disableNuxtHub ? ['@nuxthub/core'] : []),
  ],

  css: ['~/assets/css/main.css'],

  future: {
    compatibilityVersion: 4
  },

  compatibilityDate: '2024-11-27',

  colorMode: {
    storage: 'localStorage',
    preference: 'light',
  },

  hub: {
    // Enable NuxtHub features as needed
    // database: true,  // Enable D1 database
    // kv: true,        // Enable KV storage
    // blob: true,      // Enable R2 blob storage
    // cache: true,     // Enable cache
  },

  nitro: {
    preset: process.env.NITRO_PRESET || 'cloudflare-pages',
  },

  vite: {
    optimizeDeps: {
      include: ['striptags'],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
    },
  },
})
