<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { selectedSymbol, selectedExpiry, expiries, quote } from '$stores/market';
  import { marketApi, dashboardApi, ivApi } from '$api/client';
  import type { DashboardAnalytics } from '$api/types';
  import MetricCard from '$lib/components/Dashboard/MetricCard.svelte';
  import IVSmile from '$lib/components/IVCharts/IVSmile.svelte';
  import IVTermStructure from '$lib/components/IVCharts/IVTermStructure.svelte';
  import IVSurface from '$lib/components/IVCharts/IVSurface.svelte';
  import LoadingSpinner from '$lib/components/shared/LoadingSpinner.svelte';
  import { fmtPct, fmtVolume, fmtPrice } from '$utils/formatting';

  let analytics: DashboardAnalytics | null = null;
  let loading = true;

  async function load() {
    loading = true;
    try {
      const [data, data2, q] = await Promise.all([
        dashboardApi.analytics($selectedSymbol),
        marketApi.expiries($selectedSymbol),
        marketApi.quote($selectedSymbol),
      ]);
      analytics = data;
      expiries.set(data2);
      if (data2.length && !$selectedExpiry) selectedExpiry.set(data2[0].date);
      quote.set(q);
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  onMount(load);
  $: if (browser && $selectedSymbol) load();
</script>

<div class="flex flex-col h-full overflow-auto bg-terminal-bg">

  {#if loading}
    <div class="flex items-center justify-center h-32"><LoadingSpinner label="Loading analytics..." /></div>
  {:else if analytics}

    <!-- Metric cards row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-px border-b border-terminal-border shrink-0">
      <MetricCard label="ATM IV" value={analytics.atm_iv ? fmtPct(analytics.atm_iv) : '—'} accent />
      <MetricCard label="IV Rank" value={analytics.iv_rank != null ? `${analytics.iv_rank.toFixed(0)}` : '—'} sub="0–100 percentile" />
      <MetricCard label="HV 30d" value={analytics.hist_vol_30d ? fmtPct(analytics.hist_vol_30d) : '—'} />
      <MetricCard label="IV–HV Spread" value={analytics.iv_hv_spread != null ? fmtPct(analytics.iv_hv_spread) : '—'}
        valueClass={analytics.iv_hv_spread != null && analytics.iv_hv_spread > 0 ? 'text-up' : 'text-down'} />
      <MetricCard label="PCR Volume" value={analytics.pcr_volume.toFixed(2)} />
      <MetricCard label="PCR OI" value={analytics.pcr_oi.toFixed(2)} />
      <MetricCard label="Total Volume" value={fmtVolume(analytics.total_volume)} />
      <MetricCard label="Net Δ Exp" value={analytics.greeks_exposure.net_delta.toFixed(1)} sub="Open interest weighted" />
    </div>

    <!-- Charts grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px flex-1 min-h-0">

      <!-- IV Smile -->
      <div class="bg-terminal-surface border-r border-b border-terminal-border min-h-48 flex flex-col">
        <div class="px-3 py-1.5 border-b border-terminal-border shrink-0">
          <span class="text-neutral text-xxs uppercase tracking-wider">IV Smile · {$selectedExpiry}</span>
        </div>
        <div class="flex-1"><IVSmile symbol={$selectedSymbol} expiry={$selectedExpiry} /></div>
      </div>

      <!-- IV Term Structure -->
      <div class="bg-terminal-surface border-r border-b border-terminal-border min-h-48 flex flex-col">
        <div class="px-3 py-1.5 border-b border-terminal-border shrink-0">
          <span class="text-neutral text-xxs uppercase tracking-wider">IV Term Structure</span>
        </div>
        <div class="flex-1"><IVTermStructure symbol={$selectedSymbol} /></div>
      </div>

      <!-- IV Surface (3D) -->
      <div class="bg-terminal-surface border-b border-terminal-border min-h-48 flex flex-col">
        <div class="px-3 py-1.5 border-b border-terminal-border shrink-0">
          <span class="text-neutral text-xxs uppercase tracking-wider">IV Surface (3D)</span>
        </div>
        <div class="flex-1"><IVSurface symbol={$selectedSymbol} /></div>
      </div>

      <!-- Top volume calls -->
      <div class="bg-terminal-surface border-r border-terminal-border p-3">
        <h3 class="text-neutral text-xxs uppercase tracking-wider mb-2">Top Volume — Calls</h3>
        <table class="terminal-table w-full">
          <thead><tr><th class="text-left">Strike</th><th class="text-right">Volume</th></tr></thead>
          <tbody>
            {#each analytics.top_volume_calls as row}
              <tr>
                <td class="text-left font-mono">₹{row.strike}</td>
                <td class="text-right num text-up">{fmtVolume(row.volume)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Top volume puts -->
      <div class="bg-terminal-surface border-r border-terminal-border p-3">
        <h3 class="text-neutral text-xxs uppercase tracking-wider mb-2">Top Volume — Puts</h3>
        <table class="terminal-table w-full">
          <thead><tr><th class="text-left">Strike</th><th class="text-right">Volume</th></tr></thead>
          <tbody>
            {#each analytics.top_volume_puts as row}
              <tr>
                <td class="text-left font-mono">₹{row.strike}</td>
                <td class="text-right num text-down">{fmtVolume(row.volume)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Greeks exposure -->
      <div class="bg-terminal-surface p-3">
        <h3 class="text-neutral text-xxs uppercase tracking-wider mb-2">Greeks Exposure (OI-weighted)</h3>
        <div class="grid grid-cols-2 gap-2">
          {#each [
            { label: 'Net Δ', value: analytics.greeks_exposure.net_delta.toFixed(1), color: '#60A5FA' },
            { label: 'Net Γ', value: analytics.greeks_exposure.net_gamma.toFixed(3), color: '#34D399' },
            { label: 'Net ν', value: analytics.greeks_exposure.net_vega.toFixed(1), color: '#A78BFA' },
            { label: 'Net Θ', value: analytics.greeks_exposure.net_theta.toFixed(1), color: '#F87171' },
          ] as g}
            <div class="flex flex-col">
              <span class="text-xxs" style="color:{g.color}">{g.label}</span>
              <span class="font-mono font-bold text-sm num" style="color:{g.color}">{g.value}</span>
            </div>
          {/each}
        </div>
      </div>

    </div>

  {:else}
    <div class="flex items-center justify-center h-32 text-neutral text-sm">No analytics data</div>
  {/if}

</div>
