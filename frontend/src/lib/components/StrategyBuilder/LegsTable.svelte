<script lang="ts">
  import type { StrategyLeg } from '$api/types';
  import { fmtPrice } from '$utils/formatting';

  export let legs: StrategyLeg[];
</script>

<table class="terminal-table w-full text-xs">
  <thead>
    <tr>
      <th class="text-left">Action</th>
      <th class="text-left">Type</th>
      <th class="text-right">Strike</th>
      <th class="text-left">Expiry</th>
      <th class="text-right">Premium</th>
      <th class="text-right">Qty</th>
    </tr>
  </thead>
  <tbody>
    {#each legs as leg}
      <tr>
        <td class="font-semibold {leg.action === 'BUY' ? 'text-up' : 'text-down'}">{leg.action}</td>
        <td class="font-mono {leg.option_type === 'C' ? 'text-blue-400' : 'text-red-400'}">
          {leg.option_type === 'C' ? 'CALL' : 'PUT'}
        </td>
        <td class="text-right num">${leg.strike}</td>
        <td class="text-neutral">{leg.expiry}</td>
        <td class="text-right num">{leg.premium > 0 ? fmtPrice(leg.premium) : '—'}</td>
        <td class="text-right num">{leg.quantity}</td>
      </tr>
    {/each}
  </tbody>
</table>
