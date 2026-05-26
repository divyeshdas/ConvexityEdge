<script lang="ts">
  import type { ChainStrike } from '$api/types';
  import { fmtPrice, fmtGreek, fmtVolume, signClass } from '$utils/formatting';

  export let row: ChainStrike;
  export let underlying: number;

  $: c = row.call;
  $: p = row.put;
  $: isATM = row.is_atm;
  $: callITM = c?.in_the_money ?? false;
  $: putITM  = p?.in_the_money ?? false;

  function ivPctStr(iv: number | null | undefined): string {
    if (!iv) return '—';
    return `${(iv * 100).toFixed(1)}%`;
  }

  const dash = '—';
</script>

<tr class:row-atm={isATM}>
  <!-- CALLS side (right-aligned) -->
  <td class="text-right {callITM && !isATM ? 'text-slate-200' : 'text-slate-400'} num">{fmtVolume(c?.volume)}</td>
  <td class="text-right text-slate-500 num">{fmtVolume(c?.open_interest)}</td>
  <td class="text-right font-semibold num" style="color:#60A5FA">{c?.greeks ? fmtGreek(c.greeks.delta) : dash}</td>
  <td class="text-right num" style="color:#34D399">{c?.greeks ? fmtGreek(c.greeks.gamma, 4) : dash}</td>
  <td class="text-right num" style="color:#A78BFA">{c?.greeks ? fmtGreek(c.greeks.vega) : dash}</td>
  <td class="text-right num" style="color:#F87171">{c?.greeks ? fmtGreek(c.greeks.theta) : dash}</td>
  <td class="text-right text-slate-300 num">{c ? fmtPrice(c.bid) : dash}</td>
  <td class="text-right text-slate-100 font-medium num">{c ? fmtPrice(c.ask) : dash}</td>

  <!-- STRIKE column -->
  <td class="text-center font-mono font-bold px-2
    {isATM ? 'text-white text-sm' : 'text-slate-300 text-xs'}">
    {row.strike}
    {#if isATM}
      <div class="text-xxs text-accent font-normal mt-0.5">{ivPctStr(c?.implied_vol ?? p?.implied_vol)}</div>
    {/if}
  </td>

  <!-- PUTS side (left-aligned) -->
  <td class="text-left pl-2 text-slate-100 font-medium num">{p ? fmtPrice(p.bid) : dash}</td>
  <td class="text-left text-slate-300 num">{p ? fmtPrice(p.ask) : dash}</td>
  <td class="text-left {putITM && !isATM ? 'text-slate-200' : 'text-slate-400'} num">{fmtVolume(p?.volume)}</td>
  <td class="text-left text-slate-500 num">{fmtVolume(p?.open_interest)}</td>
  <td class="text-left font-semibold num" style="color:#60A5FA">{p?.greeks ? fmtGreek(p.greeks.delta) : dash}</td>
  <td class="text-left num" style="color:#34D399">{p?.greeks ? fmtGreek(p.greeks.gamma, 4) : dash}</td>
  <td class="text-left num" style="color:#A78BFA">{p?.greeks ? fmtGreek(p.greeks.vega) : dash}</td>
  <td class="text-left num" style="color:#F87171">{p?.greeks ? fmtGreek(p.greeks.theta) : dash}</td>
</tr>
