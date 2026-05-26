<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { selectedSymbol, selectedExpiry, expiries, optionChain, quote, isLoading, isStale, lastUpdated, strikeCount } from '$stores/market';
  import { startRefreshTimer, stopRefreshTimer } from '$stores/refresh';
  import { marketApi, optionsApi } from '$api/client';
  import OptionsChainTable from '$lib/components/OptionsChain/OptionsChainTable.svelte';
  import ExpirySelector from '$lib/components/shared/ExpirySelector.svelte';
  import LoadingSpinner from '$lib/components/shared/LoadingSpinner.svelte';
  import MarketChartPanel from '$lib/components/MarketChart/CandlestickChart.svelte';
  import { fmtPrice, fmtChangePct, fmtPct, fmtVolume, signClass } from '$utils/formatting';

  let error = '';
  let showChart = true;
  const STRIKES = [10, 20, 30, 40, 60];

  async function loadExpiries(sym: string) {
    try {
      const data = await marketApi.expiries(sym);
      expiries.set(data);
      if (data.length > 0 && !$selectedExpiry) {
        selectedExpiry.set(data[0].date);
      }
    } catch (e) {
      console.error('Failed to load expiries', e);
    }
  }

  async function loadChain() {
    if (!$selectedExpiry) return;
    isLoading.set(true);
    isStale.set(false);
    error = '';
    try {
      const [q, chain] = await Promise.all([
        marketApi.quote($selectedSymbol),
        optionsApi.chain($selectedSymbol, $selectedExpiry, $strikeCount),
      ]);
      quote.set(q);
      optionChain.set(chain);
      lastUpdated.set(new Date());
    } catch (e: any) {
      error = e.message ?? 'Failed to load chain';
      isStale.set(true);
    } finally {
      isLoading.set(false);
    }
  }

  // Re-load when symbol or expiry changes
  let prevSymbol = '';
  $: if ($selectedSymbol && $selectedSymbol !== prevSymbol) {
    prevSymbol = $selectedSymbol;
    selectedExpiry.set('');
    loadExpiries($selectedSymbol);
  }

  $: if ($selectedExpiry) {
    loadChain();
  }

  onMount(() => {
    loadExpiries($selectedSymbol);
    startRefreshTimer(loadChain);
  });

  onDestroy(() => stopRefreshTimer());

  // Derived stats bar values
  $: chain = $optionChain;
  $: stats = chain?.stats;
  $: q = $quote;
</script>

<div class="flex flex-col h-[calc(100vh-44px)] overflow-hidden">

  <!-- ── Stat ticker bar ─────────────────────────────────────────────────── -->
  {#if chain && stats && q}
    <div class="stat-bar shrink-0">
      <div class="stat-item">
        <span class="stat-label">Underlying</span>
        <span class="stat-value">${fmtPrice(q.price)}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Change</span>
        <span class="stat-value {q.change >= 0 ? 'positive' : 'negative'}">
          {q.change >= 0 ? '+' : ''}{fmtPrice(q.change)} ({fmtChangePct(q.change_pct)})
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">ATM IV</span>
        <span class="stat-value">{stats.atm_iv ? fmtPct(stats.atm_iv) : '—'}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">HV 30d</span>
        <span class="stat-value">{stats.hist_vol_30d ? fmtPct(stats.hist_vol_30d) : '—'}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">PCR Vol</span>
        <span class="stat-value">{stats.pcr_volume.toFixed(2)}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">PCR OI</span>
        <span class="stat-value">{stats.pcr_oi.toFixed(2)}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Call Vol</span>
        <span class="stat-value">{fmtVolume(stats.total_call_vol)}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Put Vol</span>
        <span class="stat-value">{fmtVolume(stats.total_put_vol)}</span>
      </div>
      {#if stats.iv_change_avg !== null}
        <div class="stat-item">
          <span class="stat-label">IV Chg Avg</span>
          <span class="stat-value {(stats.iv_change_avg ?? 0) < 0 ? 'highlight' : 'positive'}">
            {((stats.iv_change_avg ?? 0) * 100).toFixed(2)}%
          </span>
        </div>
      {/if}
      <div class="stat-item">
        <span class="stat-label">DTE</span>
        <span class="stat-value">{chain.dte}d</span>
      </div>
    </div>
  {/if}

  <!-- ── Toolbar ─────────────────────────────────────────────────────────── -->
  <div class="flex items-center gap-3 px-3 py-1.5 bg-terminal-surface border-b border-terminal-border shrink-0">
    <ExpirySelector compact />

    <div class="flex items-center gap-1">
      <span class="text-neutral text-xxs">Strikes</span>
      {#each STRIKES as s}
        <button
          class="px-2 py-0.5 text-xxs font-mono border transition-colors
            {$strikeCount === s
              ? 'border-accent text-accent bg-accent/10'
              : 'border-terminal-border text-neutral hover:border-slate-500'}"
          on:click={() => { strikeCount.set(s); loadChain(); }}
        >{s}</button>
      {/each}
    </div>

    <div class="flex-1"></div>

    <!-- Chart toggle -->
    <button
      class="flex items-center gap-1 px-2 py-0.5 text-xxs border border-terminal-border text-neutral hover:text-slate-300 hover:border-slate-500 transition-colors"
      on:click={() => showChart = !showChart}
    >
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {showChart ? 'Hide Chart' : 'Show Chart'}
    </button>

    {#if $isLoading}
      <LoadingSpinner size="sm" />
    {:else if $lastUpdated}
      <span class="text-neutral text-xxs font-mono">
        Updated {$lastUpdated.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })} IST
      </span>
    {/if}
  </div>

  <!-- ── Main content area ───────────────────────────────────────────────── -->
  <div class="flex flex-col flex-1 overflow-hidden">

    <!-- Chain table -->
    <div class="flex-1 overflow-auto min-h-0" style="{showChart ? 'flex: 0 0 60%' : 'flex: 1'}">
      {#if $isLoading && !chain}
        <div class="flex items-center justify-center h-32">
          <LoadingSpinner label="Loading option chain..." />
        </div>
      {:else if error}
        <div class="flex items-center justify-center h-32">
          <span class="text-down text-sm font-mono">{error}</span>
        </div>
      {:else if chain}
        <OptionsChainTable {chain} />
      {/if}
    </div>

    <!-- Chart panel -->
    {#if showChart}
      <div class="border-t border-terminal-border shrink-0" style="flex: 0 0 40%;">
        <MarketChartPanel symbol={$selectedSymbol} />
      </div>
    {/if}

  </div>
</div>
