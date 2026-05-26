<script lang="ts">
  export let label: string;
  export let value: string;
  export let sub: string = '';
  export let valueClass: string = 'text-slate-100';
  export let accent = false;
</script>

<div class="panel p-3 flex flex-col gap-1 {accent ? 'border-accent/30' : ''}">
  <span class="text-neutral text-xxs uppercase tracking-wider">{label}</span>
  <span class="font-mono font-bold text-base {valueClass} num">{value}</span>
  {#if sub}
    <span class="text-neutral text-xxs">{sub}</span>
  {/if}
</div>
