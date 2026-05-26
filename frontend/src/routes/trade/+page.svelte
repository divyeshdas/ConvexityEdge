<script lang="ts">
  import { onMount } from 'svelte';
  import { selectedSymbol, selectedExpiry, expiries, quote } from '$stores/market';
  import { marketApi } from '$api/client';
  import TradePanel from '$lib/components/TradeAnalysis/TradePanel.svelte';
  import MarketChartPanel from '$lib/components/MarketChart/CandlestickChart.svelte';
  import IVTermStructure from '$lib/components/IVCharts/IVTermStructure.svelte';

  onMount(async () => {
    if (!$selectedSymbol) return;
    const data = await marketApi.expiries($selectedSymbol);
    expiries.set(data);
    if (data.length && !$selectedExpiry) selectedExpiry.set(data[0].date);
    const q = await marketApi.quote($selectedSymbol);
    quote.set(q);
  });
</script>

<div class="flex h-[calc(100vh-44px)] gap-0 overflow-hidden">
  <!-- Trade panel (left) -->
  <TradePanel />

  <!-- Right: chart + IV term structure -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <div class="flex-1 border-b border-terminal-border overflow-hidden">
      <MarketChartPanel symbol={$selectedSymbol} />
    </div>
    <div class="h-48 bg-terminal-bg overflow-hidden">
      <div class="flex items-center px-3 py-1 border-b border-terminal-border">
        <span class="text-neutral text-xxs uppercase tracking-wider">IV Term Structure — {$selectedSymbol}</span>
      </div>
      <div class="h-full pb-6">
        <IVTermStructure symbol={$selectedSymbol} />
      </div>
    </div>
  </div>
</div>
