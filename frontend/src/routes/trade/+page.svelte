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

<div class="flex flex-col md:flex-row h-full overflow-hidden">
  <!-- Trade panel -->
  <div class="shrink-0 border-b md:border-b-0 md:border-r border-terminal-border overflow-auto max-h-72 md:max-h-none">
    <TradePanel />
  </div>

  <!-- Right: chart + IV term structure -->
  <div class="flex-1 flex flex-col overflow-hidden min-h-0">
    <div class="flex-1 border-b border-terminal-border overflow-hidden min-h-0" style="min-height: 200px;">
      <MarketChartPanel symbol={$selectedSymbol} />
    </div>
    <div class="h-48 bg-terminal-bg overflow-hidden shrink-0">
      <div class="flex items-center px-3 py-1 border-b border-terminal-border">
        <span class="text-neutral text-xxs uppercase tracking-wider">IV Term Structure — {$selectedSymbol}</span>
      </div>
      <div class="h-full pb-6">
        <IVTermStructure symbol={$selectedSymbol} />
      </div>
    </div>
  </div>
</div>
