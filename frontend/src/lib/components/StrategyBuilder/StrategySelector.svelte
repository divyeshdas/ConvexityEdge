<script lang="ts">
  export let selected: string;
  export let templates: { name: string; description: string }[] = [];

  const STRATEGY_ICONS: Record<string, string> = {
    'Long Call': '↑', 'Long Put': '↓', 'Covered Call': '→↑',
    'Protective Put': '→↓', 'Bull Call Spread': '↑→', 'Bear Put Spread': '↓→',
    'Straddle': '↕', 'Strangle': '↕↕', 'Iron Condor': '⊃',
  };
</script>

<div class="grid grid-cols-3 gap-1">
  {#each templates as t}
    <button
      class="flex flex-col items-start p-2 border text-left transition-colors
        {selected === t.name
          ? 'border-accent bg-accent/10 text-accent'
          : 'border-terminal-border text-neutral hover:border-slate-500 hover:text-slate-300'}"
      on:click={() => selected = t.name}
    >
      <span class="font-mono text-base">{STRATEGY_ICONS[t.name] ?? '○'}</span>
      <span class="text-xxs font-medium mt-1">{t.name}</span>
    </button>
  {/each}
</div>
