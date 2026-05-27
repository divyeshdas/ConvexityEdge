<script lang="ts">
  import '../app.css';
  import Navbar from '$lib/components/shared/Navbar.svelte';
  import { theme } from '$stores/theme';
  import { onMount } from 'svelte';

  // Sync theme to IST every minute
  onMount(() => {
    const handle = setInterval(() => theme.syncToIST(), 60_000);
    return () => clearInterval(handle);
  });
</script>

<!-- Mobile gate — trading terminal requires desktop -->
<div class="lg:hidden fixed inset-0 z-50 bg-terminal-bg flex flex-col items-center justify-center p-8 text-center">
  <span class="text-accent font-mono font-bold text-3xl mb-4">CE</span>
  <h1 class="text-slate-100 text-lg font-semibold mb-2">ConvexityEdge</h1>
  <p class="text-slate-400 text-sm mb-6 max-w-xs">
    This is a professional options analytics terminal built for desktop use.
  </p>
  <p class="text-slate-500 text-xs">Open on a laptop or desktop for the full experience.</p>
</div>

<div class="hidden lg:flex min-h-screen bg-terminal-bg text-slate-100 flex-col">
  <Navbar />
  <main class="flex-1 overflow-hidden">
    <slot />
  </main>
</div>
