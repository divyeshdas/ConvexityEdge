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

<div class="min-h-screen bg-terminal-bg text-slate-100 flex flex-col">
  <Navbar />
  <main class="flex-1 overflow-hidden">
    <slot />
  </main>
</div>
