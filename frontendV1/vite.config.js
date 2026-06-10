import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_DEV_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      host: env.VITE_DEV_HOST || "127.0.0.1",
      port: Number(env.VITE_DEV_PORT || 5174),
      strictPort: true,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/media": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  };
});
