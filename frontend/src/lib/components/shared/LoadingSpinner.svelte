<script lang="ts">
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let label = '';

  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };
</script>

<div class="flex items-center gap-2">
  <svg class="{sizes[size]} animate-spin text-accent" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"/>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
  </svg>
  {#if label}
    <span class="text-neutral text-xs font-mono">{label}</span>
  {/if}
</div>
