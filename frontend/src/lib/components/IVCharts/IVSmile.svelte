<script lang="ts">
  import { onMount } from 'svelte';
  import { ivApi } from '$api/client';
  import type { IVSmilePoint } from '$api/types';
  import { CHART_COLORS } from '$utils/colors';

  export let symbol: string;
  export let expiry: string;

  let chartEl: HTMLDivElement;
  let chart: any;

  async function load() {
    if (!symbol || !expiry) return;
    try {
      const data = await ivApi.smile(symbol, expiry);
      if (chart && data.length) render(data);
    } catch {}
  }

  function render(pts: IVSmilePoint[]) {
    const calls = pts.filter(p => p.option_type === 'C');
    const puts  = pts.filter(p => p.option_type === 'P');

    chart.setOption({
      backgroundColor: '#0D0F14',
      animation: false,
      grid: { left: 50, right: 20, top: 30, bottom: 40 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: CHART_COLORS.tooltip_bg,
        borderColor: CHART_COLORS.tooltip_border,
        textStyle: { color: '#CBD5E1', fontSize: 11, fontFamily: 'JetBrains Mono' },
        formatter: (p: any) => {
          const d = p[0]?.data;
          return d ? `Strike: ${d[0]}<br/>IV: ${(d[1]*100).toFixed(1)}%` : '';
        },
      },
      xAxis: {
        type: 'value', name: 'Strike',
        nameTextStyle: { color: '#475569', fontSize: 10 },
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono' },
        axisLine: { lineStyle: { color: '#252836' } },
        splitLine: { lineStyle: { color: '#1A1D27' } },
      },
      yAxis: {
        type: 'value', name: 'IV %',
        nameTextStyle: { color: '#475569', fontSize: 10 },
        axisLabel: {
          color: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono',
          formatter: (v: number) => `${(v*100).toFixed(0)}%`,
        },
        axisLine: { lineStyle: { color: '#252836' } },
        splitLine: { lineStyle: { color: '#1A1D27' } },
      },
      series: [
        {
          name: 'Calls', type: 'line', smooth: true,
          data: calls.map(p => [p.strike, p.iv]),
          lineStyle: { color: '#22C55E', width: 2 },
          itemStyle: { color: '#22C55E' }, symbol: 'circle', symbolSize: 4,
        },
        {
          name: 'Puts', type: 'line', smooth: true,
          data: puts.map(p => [p.strike, p.iv]),
          lineStyle: { color: '#EF4444', width: 2 },
          itemStyle: { color: '#EF4444' }, symbol: 'circle', symbolSize: 4,
        },
      ],
      legend: {
        top: 5, right: 10,
        textStyle: { color: '#64748B', fontSize: 10 },
        data: ['Calls', 'Puts'],
      },
    });
  }

  onMount(async () => {
    const echarts = (await import('echarts')).default;
    chart = echarts.init(chartEl, null, { renderer: 'canvas' });
    new ResizeObserver(() => chart.resize()).observe(chartEl);
    await load();
  });

  $: if (symbol && expiry && chart) load();
</script>

<div bind:this={chartEl} class="w-full h-full"></div>
