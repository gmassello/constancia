import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const api = { target: "http://localhost:8000", changeOrigin: false }

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/patients": api, "/calls": api, "/health": api, "/reset": api, "/search": api },
  },
})
