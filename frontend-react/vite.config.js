import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // En Docker sobre Windows los cambios de archivos no llegan como eventos: se revisan cada cierto tiempo
    watch: { usePolling: true },
  },
});
