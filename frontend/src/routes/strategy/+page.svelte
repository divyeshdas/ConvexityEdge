<script lang="ts">
  import { onMount } from 'svelte';
  import { selectedSymbol, selectedExpiry, expiries, quote } from '$stores/market';
  import { marketApi, strategyApi } from '$api/client';
  import type { StrategyLeg, StrategyResult } from '$api/types';
  import StrategySelector from '$lib/components/StrategyBuilder/StrategySelector.svelte';
  import LegsTable from '$lib/components/StrategyBuilder/LegsTable.svelte';
  import PayoffDiagram from '$lib/components/StrategyBuilder/PayoffDiagram.svelte';
  import ExpirySelector from '$lib/components/shared/ExpirySelector.svelte';
  import LoadingSpinner from '$lib/components/shared/LoadingSpinner.svelte';
  import { fmtCurrency, fmtPrice } from '$utils/formatting';

  let templates: { name: string; description: string }[] = [];
  let selectedStrategy = 'Straddle';
  let legs: StrategyLeg[] = [];
  let result: StrategyResult | null = null;
  let loading = false;

  async function loadExpiries() {
    if (!$selectedSymbol) return;
    const data = await marketApi.expiries($selectedSymbol);
    expiries.set(data);
    if (data.length && !$selectedExpiry) selectedExpiry.set(data[0].date);
    const q = await marketApi.quote($selectedSymbol);
    quote.set(q);
  }

  async function build() {
    if (!$selectedExpiry || !$quote) return;
    loading = true;
    try {
      const res = await strategyApi.build(selectedStrategy, $selectedSymbol, $selectedExpiry, $quote.price);
      legs   = res.legs;
      result = await strategyApi.payoff(legs);
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    templates = await strategyApi.templates();
    await loadExpiries();
  });

  $: if (selectedStrategy && $selectedExpiry && $quote) build();
</script>

<div class="flex h-[calc(100vh-44px)] gap-0 overflow-hidden">

  <!-- Left panel: strategy selector + legs -->
  <div class="w-72 shrink-0 border-r border-terminal-border flex flex-col bg-terminal-surface overflow-auto">
    <div class="px-3 py-2 border-b border-terminal-border">
      <h2 class="text-xs font-semibold text-slate-200 uppercase tracking-wider">Strategy Builder</h2>
      <p class="text-neutral text-xxs mt-0.5">{$selectedSymbol} · <ExpirySelector compact /></p>
    </div>

    <div class="p-3">
      <StrategySelector {templates} bind:selected={selectedStrategy} />
    </div>

    {#if templates.find(t => t.name === selectedStrategy)}
      <div class="px-3 pb-2">
        <p class="text-neutral text-xxs italic">
          {templates.find(t => t.name === selectedStrategy)?.description}
        </p>
      </div>
    {/if}

    {#if legs.length}
      <div class="px-3 pb-3 border-t border-terminal-border pt-2">
        <h3 class="text-neutral text-xxs uppercase tracking-wider mb-2">Legs</h3>
        <LegsTable {legs} />
      </div>
    {/if}

    {#if loading}<div class="px-3"><LoadingSpinner size="sm" /></div>{/if}
  </div>

  <!-- Main: payoff diagram + metrics -->
  <div class="flex-1 flex flex-col overflow-hidden">
    {#if result}
      <!-- Metric cards -->
      <div class="flex gap-0 border-b border-terminal-border shrink-0">
        {#each [
          { label: 'Net Premium', value: fmtCurrency(result.net_premium), cls: result.net_premium >= 0 ? 'text-up' : 'text-down' },
          { label: 'Max Profit',  value: result.max_profit != null ? fmtCurrency(result.max_profit) : '∞', cls: 'text-up' },
          { label: 'Max Loss',    value: result.max_loss != null ? fmtCurrency(result.max_loss) : '∞', cls: 'text-down' },
          { label: 'Risk/Reward', value: result.risk_reward != null ? `${result.risk_reward}x` : '—', cls: 'text-warning' },
          { label: 'Exp. Move',   value: `±${fmtCurrency(result.expected_move)}`, cls: 'text-accent' },
          { label: 'Break-Evens', value: result.break_evens.map(b => `$${b}`).join(' / ') || '—', cls: 'text-slate-300' },
        ] as card}
          <div class="flex flex-col px-4 py-2 border-r border-terminal-border">
            <span class="text-neutral text-xxs uppercase tracking-wider">{card.label}</span>
            <span class="font-mono font-bold text-sm {card.cls} num">{card.value}</span>
          </div>
        {/each}
      </div>

      <!-- Payoff chart -->
      <div class="flex-1 p-2">
        <PayoffDiagram {result} underlying={$quote?.price ?? 0} />
      </div>
    {:else if loading}
      <div class="flex items-center justify-center flex-1">
        <LoadingSpinner label="Building strategy..." />
      </div>
    {:else}
      <div class="flex items-center justify-center flex-1 text-neutral text-sm">
        Select a strategy to view payoff
      </div>
    {/if}
  </div>

</div>
