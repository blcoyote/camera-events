import { defineConfig, loadEnv, normalizePath } from "vite";
import react from "@vitejs/plugin-react-swc";
import { VitePWA } from "vite-plugin-pwa";
import { viteStaticCopy } from "vite-plugin-static-copy";
import path from "node:path";

export default ({ mode }: { mode: string }) => {
  process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };
  // https://vitejs.dev/config/
  return defineConfig({
    server: {
      port: 3000,
      proxy: {
        "/api": {
          protocolRewrite: "https",
          target: process.env.VITE_BaseURL_DEV,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
      },
    },
    plugins: [
      viteStaticCopy({
        targets: [
          {
            src: normalizePath(
              `${path.resolve(__dirname, ".")}/firebase-messaging-sw.js`
            ),
            dest: normalizePath(`${path.resolve(__dirname, "./dist")}`),
            overwrite: true,
          },
        ],
      }),
      react(),
      VitePWA({
        registerType: "autoUpdate",
        injectRegister: "auto", // I register SW in app.ts, disable auto registration
        // minimum PWA
        includeAssets: [
          "favicon.ico",
          "robots.txt",
          "*.svg",
          "*.{png,ico}",
          "*.{json}",
          "*.js",
        ],
        devOptions: {
          enabled: true,
          /* other options */
        },
        workbox: {},
      }),
    ],
    optimizeDeps: {
      esbuildOptions: {
        target: "esnext",
      },
    },
    build: {
      target: "esnext",
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            // creating a chunk to react routes deps. Reducing the vendor chunk size
            if (
              id.includes("react-router-dom") ||
              id.includes("react-router")
            ) {
              return "@react-router";
            }
            if (id.includes("tanstack")) {
              return "@tanstack";
            }
            if (id.includes("firebase")) {
              return "@firebase";
            }
            if (id.includes("motion")) {
              return "@motion";
            }
          },
        },
      },
    },
  });
};
