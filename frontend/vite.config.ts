import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  resolve: {
    conditions: ['browser', 'module', 'svelte', 'default'],
  },
  optimizeDeps: {
    include: ['svelte', 'echarts'],
    esbuildOptions: {
      conditions: ['browser', 'module', 'svelte', 'default'],
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.PUBLIC_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
