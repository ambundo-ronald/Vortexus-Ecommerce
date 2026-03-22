// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: false },

  modules: ['@nuxt/ui', '@nuxt/eslint', 'nuxt-charts', '@nuxthub/core'],

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
    preset: 'cloudflare-pages',
  },
})