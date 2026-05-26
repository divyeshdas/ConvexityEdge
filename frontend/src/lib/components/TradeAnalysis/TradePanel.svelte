<script lang="ts">
  import { selectedSymbol, selectedExpiry, quote } from '$stores/market';
  import { tradeApi } from '$api/client';
  import type { TradeAnalysisResult } from '$api/types';
  import { fmtCurrency, fmtPrice } from '$utils/formatting';

  let entryPrice  = '';
  let impliedVol  = '';
  let presetLevels = '5';
  let initialSize  = '1';
  let subSize      = '1';
  let volFloor: 'daily' | 'weekly' | 'monthly' = 'monthly';

  let result: TradeAnalysisResult | null = null;
  let loading = false;
  let error   = '';

  // Auto-fill entry price from quote
  $: if ($quote && !entryPrice) entryPrice = $quote.price.toFixed(2);

  async function analyze() {
    if (!entryPrice || !impliedVol || !$selectedExpiry) return;
    loading = true;
    error   = '';
    result  = null;
    try {
      result = await tradeApi.analyze({
        symbol:          $selectedSymbol,
        entry_price:     parseFloat(entryPrice),
        implied_vol:     parseFloat(impliedVol) / 100,
        expiry:          $selectedExpiry,
        preset_levels:   parseInt(presetLevels),
        initial_size:    parseInt(initialSize),
        subsequent_size: parseInt(subSize),
        vol_floor:       volFloor,
      });
    } catch (e: any) {
      error = e.message ?? 'Analysis failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="bg-terminal-panel border border-terminal-border p-0 w-72 shrink-0">
  <!-- Header -->
  <div class="flex items-center justify-between px-3 py-2 border-b border-terminal-border bg-terminal-surface">
    <span class="text-xs font-semibold text-slate-200">
      {$selectedSymbol ? `${$selectedSymbol}` : 'No Ticker'} — Trade Analysis
    </span>
  </div>

  <div class="p-3 flex flex-col gap-4">

    <!-- ScaleOrder Settings -->
    <div class="flex flex-col gap-2">
      <span class="text-neutral text-xxs uppercase tracking-wider font-semibold border-b border-terminal-border pb-1">
        Scale Settings
      </span>

      <div class="grid grid-cols-2 gap-x-2 gap-y-1.5">
        <label class="text-neutral text-xxs">Preset Levels:</label>
        <input class="trade-input" type="number" bind:value={presetLevels} min="1" max="100" />

        <label class="text-neutral text-xxs">Initial Size:</label>
        <input class="trade-input" type="number" bind:value={initialSize} min="1" />

        <label class="text-neutral text-xxs">Subsequent Size:</label>
        <input class="trade-input" type="number" bind:value={subSize} min="1" />

        <label class="text-neutral text-xxs">Vol Floor:</label>
        <select class="trade-input" bind:value={volFloor}>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
      </div>
    </div>

    <!-- Trade Analysis inputs -->
    <div class="flex flex-col gap-2">
      <span class="text-neutral text-xxs uppercase tracking-wider font-semibold border-b border-terminal-border pb-1">
        Trade Analysis
      </span>

      <div class="grid grid-cols-2 gap-x-2 gap-y-1.5">
        <label class="text-neutral text-xxs">Entry Price:</label>
        <input class="trade-input" type="number" step="0.01" bind:value={entryPrice} placeholder="244.00" />

        <label class="text-neutral text-xxs">Implied Vol (%):</label>
        <input class="trade-input" type="number" step="0.1" bind:value={impliedVol} placeholder="42" />
      </div>

      <button class="trade-btn-primary mt-1" on:click={analyze} disabled={loading}>
        {loading ? 'Analyzing…' : 'Analyze Trade'}
      </button>
    </div>

    <!-- Results -->
    {#if error}
      <p class="text-down text-xxs font-mono">{error}</p>
    {:else if result}
      <div class="flex flex-col gap-1 border-t border-terminal-border pt-3">
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">Est. Floor Value:</span>
          <span class="num text-slate-200 text-xs font-semibold">{fmtCurrency(result.floor_value)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">Floor %:</span>
          <span class="num text-down text-xs">-{result.floor_pct.toFixed(2)}%</span>
        </div>
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">Max Cash Alloc:</span>
          <span class="num text-slate-200 text-xs font-semibold">{fmtCurrency(result.max_cash_allocation)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">Profit / Level:</span>
          <span class="num text-up text-xs font-semibold">{fmtCurrency(result.profit_per_level)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">All-Level Profit:</span>
          <span class="num text-up text-xs font-bold text-sm">{fmtCurrency(result.all_level_profit)}</span>
        </div>
        <div class="flex justify-between mt-1 border-t border-terminal-border pt-1">
          <span class="text-neutral text-xxs">Expected Move:</span>
          <span class="num text-accent text-xs">±{fmtCurrency(result.expected_move)} ({result.expected_move_pct.toFixed(1)}%)</span>
        </div>
        <div class="flex justify-between">
          <span class="text-neutral text-xxs">Risk / Reward:</span>
          <span class="num text-warning text-xs">{result.risk_reward.toFixed(2)}x</span>
        </div>
      </div>
    {:else}
      <div class="flex flex-col gap-1 border-t border-terminal-border pt-2">
        {#each ['Est. Floor Value','Est. Max Cash Allocation','Est. Profit per Level','Est. All-Level Profit'] as lbl}
          <div class="flex justify-between">
            <span class="text-neutral text-xxs">{lbl}:</span>
            <span class="text-neutral text-xxs">null</span>
          </div>
        {/each}
      </div>
    {/if}

  </div>
</div>
