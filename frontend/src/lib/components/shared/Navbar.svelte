<script lang="ts">
  import { page } from '$app/stores';
  import { theme } from '$stores/theme';
  import { selectedSymbol, lastUpdated, isStale, nextRefreshIn } from '$stores/market';
  import SymbolSearch from './SymbolSearch.svelte';

  const navLinks = [
    { href: '/chain',    label: 'Chain' },
    { href: '/strategy', label: 'Strategy' },
    { href: '/dashboard',label: 'Analytics' },
    { href: '/trade',    label: 'Trade' },
  ];

  $: currentPath = $page.url.pathname;
  $: formattedTime = $lastUpdated
    ? $lastUpdated.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })
    : null;
</script>

<nav class="h-11 bg-terminal-surface border-b border-terminal-border flex items-center gap-0 select-none z-50 relative">
  <!-- Logo -->
  <a href="/chain" class="flex items-center gap-2 px-4 border-r border-terminal-border h-full shrink-0 hover:bg-terminal-panel transition-colors">
    <span class="text-accent font-mono font-bold text-sm tracking-wider">CE</span>
    <span class="text-slate-300 font-sans text-xs font-semibold tracking-wide hidden sm:inline">ConvexityEdge</span>
  </a>

  <!-- Symbol search -->
  <div class="flex items-center px-3 border-r border-terminal-border h-full">
    <SymbolSearch />
  </div>

  <!-- Nav links -->
  <div class="flex items-center h-full">
    {#each navLinks as link}
      <a
        href={link.href}
        class="flex items-center h-full px-4 text-xs font-medium tracking-wide transition-colors border-r border-terminal-border
          {currentPath.startsWith(link.href)
            ? 'text-accent border-b-2 border-b-accent bg-terminal-panel'
            : 'text-slate-400 hover:text-slate-200 hover:bg-terminal-panel'}"
      >
        {link.label}
      </a>
    {/each}
  </div>

  <!-- Spacer -->
  <div class="flex-1"></div>

  <!-- Refresh counter -->
  <div class="flex items-center gap-2 px-3 border-l border-terminal-border h-full">
    {#if $isStale}
      <span class="stale-badge">STALE</span>
    {:else if formattedTime}
      <span class="text-neutral text-xxs font-mono">{formattedTime} IST</span>
      <div class="w-5 h-5 relative">
        <svg class="w-5 h-5 -rotate-90" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="8" fill="none" stroke="#252836" stroke-width="2"/>
          <circle
            cx="10" cy="10" r="8" fill="none"
            stroke="#3B82F6" stroke-width="2"
            stroke-dasharray="{50.27}"
            stroke-dashoffset="{50.27 * (1 - $nextRefreshIn / 60)}"
            class="transition-all duration-1000"
          />
        </svg>
      </div>
      <span class="text-neutral text-xxs font-mono">{$nextRefreshIn}s</span>
    {/if}
  </div>

  <!-- Theme toggle -->
  <button
    on:click={() => theme.toggle()}
    class="flex items-center justify-center w-10 h-full border-l border-terminal-border text-slate-400 hover:text-slate-200 hover:bg-terminal-panel transition-colors"
    title="Toggle theme"
  >
    {#if $theme === 'dark'}
      <!-- Sun icon -->
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="4" stroke-width="2"/>
        <path stroke-width="2" stroke-linecap="round" d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
      </svg>
    {:else}
      <!-- Moon icon -->
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-width="2" stroke-linecap="round" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    {/if}
  </button>
</nav>
