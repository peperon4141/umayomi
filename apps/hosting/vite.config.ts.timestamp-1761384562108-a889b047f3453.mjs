// vite.config.ts
import { defineConfig, loadEnv } from "file:///Users/soichiro/Dev/umayomi/node_modules/.pnpm/vite@5.4.21_@types+node@20.19.23_lightningcss@1.30.2_sass@1.93.2/node_modules/vite/dist/node/index.js";
import vue from "file:///Users/soichiro/Dev/umayomi/node_modules/.pnpm/@vitejs+plugin-vue@5.2.4_vite@5.4.21_@types+node@20.19.23_lightningcss@1.30.2_sass@1.93.2__vue@3.5.22_typescript@5.9.3_/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import tailwindcss from "file:///Users/soichiro/Dev/umayomi/node_modules/.pnpm/@tailwindcss+vite@4.1.15_vite@5.4.21_@types+node@20.19.23_lightningcss@1.30.2_sass@1.93.2_/node_modules/@tailwindcss/vite/dist/index.mjs";
import Components from "file:///Users/soichiro/Dev/umayomi/node_modules/.pnpm/unplugin-vue-components@28.8.0_@babel+parser@7.28.4_vue@3.5.22_typescript@5.9.3_/node_modules/unplugin-vue-components/dist/vite.js";
import { PrimeVueResolver } from "file:///Users/soichiro/Dev/umayomi/node_modules/.pnpm/@primevue+auto-import-resolver@4.4.1/node_modules/@primevue/auto-import-resolver/index.mjs";
import { fileURLToPath, URL } from "node:url";
var __vite_injected_original_import_meta_url = "file:///Users/soichiro/Dev/umayomi/apps/hosting/vite.config.ts";
var vite_config_default = defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [
      vue(),
      tailwindcss(),
      Components({
        resolvers: [PrimeVueResolver()]
      })
    ],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
      }
    },
    server: {
      port: 3100,
      host: "127.0.0.1"
    },
    build: {
      outDir: "../firebase/hosting_contents",
      emptyOutDir: true
    },
    define: {
      // 環境変数をViteで利用可能にする
      "import.meta.env.VITE_FIREBASE_API_KEY": JSON.stringify(env.VITE_FIREBASE_API_KEY),
      "import.meta.env.VITE_FIREBASE_AUTH_DOMAIN": JSON.stringify(env.VITE_FIREBASE_AUTH_DOMAIN),
      "import.meta.env.VITE_FIREBASE_PROJECT_ID": JSON.stringify(env.VITE_FIREBASE_PROJECT_ID),
      "import.meta.env.VITE_FIREBASE_STORAGE_BUCKET": JSON.stringify(env.VITE_FIREBASE_STORAGE_BUCKET),
      "import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID": JSON.stringify(env.VITE_FIREBASE_MESSAGING_SENDER_ID),
      "import.meta.env.VITE_FIREBASE_APP_ID": JSON.stringify(env.VITE_FIREBASE_APP_ID),
      "import.meta.env.VITE_FIREBASE_MEASUREMENT_ID": JSON.stringify(env.VITE_FIREBASE_MEASUREMENT_ID),
      "import.meta.env.VITE_USE_FIREBASE_EMULATOR": JSON.stringify(env.VITE_USE_FIREBASE_EMULATOR)
    }
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvVXNlcnMvc29pY2hpcm8vRGV2L3VtYXlvbWkvYXBwcy9ob3N0aW5nXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvVXNlcnMvc29pY2hpcm8vRGV2L3VtYXlvbWkvYXBwcy9ob3N0aW5nL3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9Vc2Vycy9zb2ljaGlyby9EZXYvdW1heW9taS9hcHBzL2hvc3Rpbmcvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcsIGxvYWRFbnYgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgdGFpbHdpbmRjc3MgZnJvbSAnQHRhaWx3aW5kY3NzL3ZpdGUnXG5pbXBvcnQgQ29tcG9uZW50cyBmcm9tICd1bnBsdWdpbi12dWUtY29tcG9uZW50cy92aXRlJ1xuaW1wb3J0IHsgUHJpbWVWdWVSZXNvbHZlciB9IGZyb20gJ0BwcmltZXZ1ZS9hdXRvLWltcG9ydC1yZXNvbHZlcidcbmltcG9ydCB7IGZpbGVVUkxUb1BhdGgsIFVSTCB9IGZyb20gJ25vZGU6dXJsJ1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoKHsgbW9kZSB9KSA9PiB7XG4gIC8vIFx1NzRCMFx1NTg4M1x1NTkwOVx1NjU3MFx1MzA5Mlx1OEFBRFx1MzA3Rlx1OEZCQ1x1MzA3RlxuICBjb25zdCBlbnYgPSBsb2FkRW52KG1vZGUsIHByb2Nlc3MuY3dkKCksICcnKVxuICBcbiAgcmV0dXJuIHtcbiAgICBwbHVnaW5zOiBbXG4gICAgICB2dWUoKSxcbiAgICAgIHRhaWx3aW5kY3NzKCksXG4gICAgICBDb21wb25lbnRzKHtcbiAgICAgICAgcmVzb2x2ZXJzOiBbUHJpbWVWdWVSZXNvbHZlcigpXSxcbiAgICAgIH0pLFxuICAgIF0sXG4gICAgcmVzb2x2ZToge1xuICAgICAgYWxpYXM6IHtcbiAgICAgICAgJ0AnOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vc3JjJywgaW1wb3J0Lm1ldGEudXJsKSksXG4gICAgICB9LFxuICAgIH0sXG4gICAgc2VydmVyOiB7XG4gICAgICBwb3J0OiAzMTAwLFxuICAgICAgaG9zdDogJzEyNy4wLjAuMScsXG4gICAgfSxcbiAgICBidWlsZDoge1xuICAgICAgb3V0RGlyOiAnLi4vZmlyZWJhc2UvaG9zdGluZ19jb250ZW50cycsXG4gICAgICBlbXB0eU91dERpcjogdHJ1ZSxcbiAgICB9LFxuICAgIGRlZmluZToge1xuICAgICAgLy8gXHU3NEIwXHU1ODgzXHU1OTA5XHU2NTcwXHUzMDkyVml0ZVx1MzA2N1x1NTIyOVx1NzUyOFx1NTNFRlx1ODBGRFx1MzA2Qlx1MzA1OVx1MzA4QlxuICAgICAgJ2ltcG9ydC5tZXRhLmVudi5WSVRFX0ZJUkVCQVNFX0FQSV9LRVknOiBKU09OLnN0cmluZ2lmeShlbnYuVklURV9GSVJFQkFTRV9BUElfS0VZKSxcbiAgICAgICdpbXBvcnQubWV0YS5lbnYuVklURV9GSVJFQkFTRV9BVVRIX0RPTUFJTic6IEpTT04uc3RyaW5naWZ5KGVudi5WSVRFX0ZJUkVCQVNFX0FVVEhfRE9NQUlOKSxcbiAgICAgICdpbXBvcnQubWV0YS5lbnYuVklURV9GSVJFQkFTRV9QUk9KRUNUX0lEJzogSlNPTi5zdHJpbmdpZnkoZW52LlZJVEVfRklSRUJBU0VfUFJPSkVDVF9JRCksXG4gICAgICAnaW1wb3J0Lm1ldGEuZW52LlZJVEVfRklSRUJBU0VfU1RPUkFHRV9CVUNLRVQnOiBKU09OLnN0cmluZ2lmeShlbnYuVklURV9GSVJFQkFTRV9TVE9SQUdFX0JVQ0tFVCksXG4gICAgICAnaW1wb3J0Lm1ldGEuZW52LlZJVEVfRklSRUJBU0VfTUVTU0FHSU5HX1NFTkRFUl9JRCc6IEpTT04uc3RyaW5naWZ5KGVudi5WSVRFX0ZJUkVCQVNFX01FU1NBR0lOR19TRU5ERVJfSUQpLFxuICAgICAgJ2ltcG9ydC5tZXRhLmVudi5WSVRFX0ZJUkVCQVNFX0FQUF9JRCc6IEpTT04uc3RyaW5naWZ5KGVudi5WSVRFX0ZJUkVCQVNFX0FQUF9JRCksXG4gICAgICAnaW1wb3J0Lm1ldGEuZW52LlZJVEVfRklSRUJBU0VfTUVBU1VSRU1FTlRfSUQnOiBKU09OLnN0cmluZ2lmeShlbnYuVklURV9GSVJFQkFTRV9NRUFTVVJFTUVOVF9JRCksXG4gICAgICAnaW1wb3J0Lm1ldGEuZW52LlZJVEVfVVNFX0ZJUkVCQVNFX0VNVUxBVE9SJzogSlNPTi5zdHJpbmdpZnkoZW52LlZJVEVfVVNFX0ZJUkVCQVNFX0VNVUxBVE9SKSxcbiAgICB9LFxuICB9XG59KVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUEwUyxTQUFTLGNBQWMsZUFBZTtBQUNoVixPQUFPLFNBQVM7QUFDaEIsT0FBTyxpQkFBaUI7QUFDeEIsT0FBTyxnQkFBZ0I7QUFDdkIsU0FBUyx3QkFBd0I7QUFDakMsU0FBUyxlQUFlLFdBQVc7QUFMcUosSUFBTSwyQ0FBMkM7QUFPek8sSUFBTyxzQkFBUSxhQUFhLENBQUMsRUFBRSxLQUFLLE1BQU07QUFFeEMsUUFBTSxNQUFNLFFBQVEsTUFBTSxRQUFRLElBQUksR0FBRyxFQUFFO0FBRTNDLFNBQU87QUFBQSxJQUNMLFNBQVM7QUFBQSxNQUNQLElBQUk7QUFBQSxNQUNKLFlBQVk7QUFBQSxNQUNaLFdBQVc7QUFBQSxRQUNULFdBQVcsQ0FBQyxpQkFBaUIsQ0FBQztBQUFBLE1BQ2hDLENBQUM7QUFBQSxJQUNIO0FBQUEsSUFDQSxTQUFTO0FBQUEsTUFDUCxPQUFPO0FBQUEsUUFDTCxLQUFLLGNBQWMsSUFBSSxJQUFJLFNBQVMsd0NBQWUsQ0FBQztBQUFBLE1BQ3REO0FBQUEsSUFDRjtBQUFBLElBQ0EsUUFBUTtBQUFBLE1BQ04sTUFBTTtBQUFBLE1BQ04sTUFBTTtBQUFBLElBQ1I7QUFBQSxJQUNBLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxNQUNSLGFBQWE7QUFBQSxJQUNmO0FBQUEsSUFDQSxRQUFRO0FBQUE7QUFBQSxNQUVOLHlDQUF5QyxLQUFLLFVBQVUsSUFBSSxxQkFBcUI7QUFBQSxNQUNqRiw2Q0FBNkMsS0FBSyxVQUFVLElBQUkseUJBQXlCO0FBQUEsTUFDekYsNENBQTRDLEtBQUssVUFBVSxJQUFJLHdCQUF3QjtBQUFBLE1BQ3ZGLGdEQUFnRCxLQUFLLFVBQVUsSUFBSSw0QkFBNEI7QUFBQSxNQUMvRixxREFBcUQsS0FBSyxVQUFVLElBQUksaUNBQWlDO0FBQUEsTUFDekcsd0NBQXdDLEtBQUssVUFBVSxJQUFJLG9CQUFvQjtBQUFBLE1BQy9FLGdEQUFnRCxLQUFLLFVBQVUsSUFBSSw0QkFBNEI7QUFBQSxNQUMvRiw4Q0FBOEMsS0FBSyxVQUFVLElBQUksMEJBQTBCO0FBQUEsSUFDN0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
