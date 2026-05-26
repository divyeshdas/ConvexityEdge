<script lang="ts">
  import { onMount } from 'svelte';
  import type { StrategyResult } from '$api/types';
  import { CHART_COLORS } from '$utils/colors';

  export let result: StrategyResult;
  export let underlying: number;

  let chartEl: HTMLDivElement;
  let chart: any;

  function render() {
    if (!chart || !result?.payoff_curve?.length) return;

    const prices = result.payoff_curve.map(p => p.price);
    const pnls   = result.payoff_curve.map(p => p.pnl);
    const colors = pnls.map(v => v >= 0 ? 'rgba(34,197,94,0.8)' : 'rgba(239,68,68,0.8)');

    // Zero line reference
    const zeroLine = prices.map(p => 0);

    chart.setOption({
      backgroundColor: '#0D0F14',
      animation: false,
      grid: { left: 55, right: 20, top: 20, bottom: 40 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: CHART_COLORS.tooltip_bg,
        borderColor: CHART_COLORS.tooltip_border,
        textStyle: { color: '#CBD5E1', fontSize: 11, fontFamily: 'JetBrains Mono' },
        formatter: (params: any) => {
          const price = params[0]?.axisValue;
          const pnl   = params[0]?.data;
          return `Price: $${price}<br/>P&L: <b style="color:${pnl >= 0 ? '#22C55E' : '#EF4444'}">$${Number(pnl).toFixed(2)}</b>`;
        },
      },
      xAxis: {
        type: 'category', data: prices.map(p => p.toFixed(0)),
        axisLabel: { color: '#64748B', fontSize: 9, fontFamily: 'JetBrains Mono', interval: Math.floor(prices.length / 8) },
        axisLine: { lineStyle: { color: '#252836' } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#64748B', fontSize: 9, fontFamily: 'JetBrains Mono',
          formatter: (v: number) => `$${v.toFixed(0)}`,
        },
        axisLine: { lineStyle: { color: '#252836' } },
        splitLine: { lineStyle: { color: '#1A1D27' } },
      },
      series: [
        {
          type: 'line', data: pnls, smooth: false, symbol: 'none',
          lineStyle: { width: 2 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(34,197,94,0.15)' },
                { offset: 1, color: 'rgba(239,68,68,0.05)' },
              ],
            },
          },
          itemStyle: { color: '#3B82F6' },
          // Color line based on sign
          markLine: {
            silent: true,
            data: [
              {
                yAxis: 0,
                lineStyle: { color: '#475569', type: 'dashed', width: 1 },
                label: { show: false },
              },
              {
                xAxis: prices.findIndex(p => Math.abs(p - underlying) < (prices[1] - prices[0]) * 1.5),
                lineStyle: { color: '#3B82F6', type: 'dashed', width: 1 },
                label: { show: true, formatter: 'Spot', color: '#3B82F6', fontSize: 9, fontFamily: 'JetBrains Mono' },
              },
              ...result.break_evens.map(be => ({
                xAxis: prices.findIndex(p => Math.abs(p - be) < (prices[1] - prices[0]) * 1.5),
                lineStyle: { color: '#F59E0B', type: 'dashed', width: 1 },
                label: { show: true, formatter: `BE $${be}`, color: '#F59E0B', fontSize: 9, fontFamily: 'JetBrains Mono' },
              })),
            ],
          },
        },
      ],
    });
  }

  onMount(async () => {
    const echarts = (await import('echarts')).default;
    chart = echarts.init(chartEl, null, { renderer: 'canvas' });
    new ResizeObserver(() => chart.resize()).observe(chartEl);
    render();
  });

  $: if (result && chart) render();
</script>

<div bind:this={chartEl} class="w-full h-full"></div>
