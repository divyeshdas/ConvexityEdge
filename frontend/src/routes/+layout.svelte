<script lang="ts">
  import '../app.css';
  import Navbar from '$lib/components/shared/Navbar.svelte';
  import { theme } from '$stores/theme';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  onMount(() => {
    const handle = setInterval(() => theme.syncToIST(), 60_000);
    return () => clearInterval(handle);
  });

  const navLinks = [
    { href: '/chain',     label: 'Chain',     icon: 'M3 10h18M3 14h18M10 3v18M14 3v18' },
    { href: '/strategy',  label: 'Strategy',  icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5' },
    { href: '/dashboard', label: 'Analytics', icon: 'M18 20V10M12 20V4M6 20v-6' },
    { href: '/trade',     label: 'Trade',     icon: 'M22 7l-9.5 9.5-5-5L2 17M16 7h6v6' },
  ];

  $: currentPath = $page.url.pathname;
</script>

<div class="min-h-screen bg-terminal-bg text-slate-100 flex flex-col">
  <Navbar />
  <main class="flex-1 min-h-0 overflow-auto pb-14 md:pb-0 md:overflow-hidden">
    <slot />
  </main>

  <!-- Bottom tab bar — mobile only -->
  <nav class="fixed bottom-0 left-0 right-0 h-14 bg-terminal-surface border-t border-terminal-border flex md:hidden z-40">
    {#each navLinks as link}
      <a
        href={link.href}
        class="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors
          {currentPath.startsWith(link.href)
            ? 'text-accent'
            : 'text-slate-500 hover:text-slate-300'}"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="{link.icon}" />
        </svg>
        <span class="text-xxs font-medium">{link.label}</span>
      </a>
    {/each}
  </nav>
</div>
