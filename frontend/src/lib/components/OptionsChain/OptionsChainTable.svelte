<script lang="ts">
  import type { OptionChain, ChainStrike } from '$api/types';
  import { fmtPrice, fmtGreek, fmtPct, fmtVolume, fmtChange, signClass } from '$utils/formatting';
  import ChainRow from './ChainRow.svelte';

  export let chain: OptionChain;

  // Column definitions for each side
  const callCols = ['volume','oi','delta','gamma','vega','theta','bid','ask'];
  const putCols  = ['bid','ask','volume','oi','delta','gamma','vega','theta'];
</script>

<div class="w-full overflow-x-auto">
  <table class="terminal-table w-full text-right">
    <colgroup>
      <!-- Call columns -->
      <col class="w-16"/><col class="w-16"/>
      <col class="w-16"/><col class="w-14"/>
      <col class="w-14"/><col class="w-14"/>
      <col class="w-14"/><col class="w-14"/>
      <!-- Strike -->
      <col class="w-20"/>
      <!-- Put columns -->
      <col class="w-14"/><col class="w-14"/>
      <col class="w-16"/><col class="w-16"/>
      <col class="w-16"/><col class="w-14"/>
      <col class="w-14"/><col class="w-14"/>
    </colgroup>
    <thead>
      <tr>
        <!-- CALLS header (right-aligned, reversed order visually) -->
        <th class="text-right text-slate-500 !text-xxs">VOLUME</th>
        <th class="text-right text-slate-500 !text-xxs">OI</th>
        <th class="text-right text-delta !text-xxs">DELTA</th>
        <th class="text-right text-gamma !text-xxs">GAMMA</th>
        <th class="text-right text-vega !text-xxs">VEGA</th>
        <th class="text-right text-theta !text-xxs">THETA</th>
        <th class="text-right text-slate-400 !text-xxs">BID</th>
        <th class="text-right text-slate-300 !text-xxs">ASK</th>

        <!-- STRIKE -->
        <th class="text-center !text-xs text-slate-300 font-semibold bg-terminal-panel">STRIKE</th>

        <!-- PUTS header -->
        <th class="text-left text-slate-300 !text-xxs pl-2">BID</th>
        <th class="text-left text-slate-400 !text-xxs">ASK</th>
        <th class="text-left text-slate-500 !text-xxs">VOLUME</th>
        <th class="text-left text-slate-500 !text-xxs">OI</th>
        <th class="text-left text-delta !text-xxs">DELTA</th>
        <th class="text-left text-gamma !text-xxs">GAMMA</th>
        <th class="text-left text-vega !text-xxs">VEGA</th>
        <th class="text-left text-theta !text-xxs">THETA</th>
      </tr>
      <!-- Section labels row -->
      <tr class="border-b-2 border-terminal-muted">
        <th colspan="8" class="text-center text-slate-400 !text-xxs pb-1 tracking-widest uppercase">
          — CALLS —
        </th>
        <th class="bg-terminal-panel opacity-60"></th>
        <th colspan="8" class="text-center text-slate-400 !text-xxs pb-1 tracking-widest uppercase">
          — PUTS —
        </th>
      </tr>
    </thead>
    <tbody>
      {#each chain.strikes as row (row.strike)}
        <ChainRow {row} underlying={chain.underlying} />
      {/each}
    </tbody>
  </table>
</div>

<style>
  .text-delta { color: #60A5FA; }
  .text-gamma { color: #34D399; }
  .text-vega  { color: #A78BFA; }
  .text-theta { color: #F87171; }
</style>
