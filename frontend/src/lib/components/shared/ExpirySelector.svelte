<script lang="ts">
  import { selectedExpiry, expiries } from '$stores/market';

  export let compact = false;
</script>

<div class="flex items-center gap-1">
  {#if !compact}
    <span class="text-neutral text-xxs uppercase tracking-wider">Expiry</span>
  {/if}
  <select
    class="bg-terminal-bg border border-terminal-border text-slate-200 font-mono text-xs
           px-2 py-1 outline-none focus:border-accent cursor-pointer"
    bind:value={$selectedExpiry}
  >
    {#each $expiries as exp}
      <option value={exp.date}>{exp.label}</option>
    {/each}
  </select>
</div>
