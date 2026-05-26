<script lang="ts">
  import { isStale, lastUpdated } from '$stores/market';

  $: timeStr = $lastUpdated
    ? $lastUpdated.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })
    : '—';
</script>

{#if $isStale}
  <span class="stale-badge">DATA STALE</span>
{:else if $lastUpdated}
  <span class="text-neutral text-xxs font-mono">{timeStr} IST</span>
{/if}
