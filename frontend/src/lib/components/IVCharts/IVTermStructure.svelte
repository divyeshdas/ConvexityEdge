<script lang="ts">
  import { onMount } from 'svelte';
  import { ivApi } from '$api/client';
  import { CHART_COLORS } from '$utils/colors';

  export let symbol: string;

  let chartEl: HTMLDivElement;
  let chart: any;

  async function load() {
    if (!symbol) return;
    try {
      const data = await ivApi.termStructure(symbol);
      if (chart && data.length) {
        chart.setOption({
          backgroundColor: '#000000',
          animation: false,
          grid: { left: 50, right: 20, top: 30, bottom: 40 },
          tooltip: {
            trigger: 'axis',
            confine: true,
            appendToBody: true,
            backgroundColor: CHART_COLORS.tooltip_bg,
            borderColor: CHART_COLORS.tooltip_border,
            borderWidth: 1,
            padding: [8, 12],
            textStyle: { color: '#CBD5E1', fontSize: 11, fontFamily: 'Inter' },
            extraCssText: 'border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); z-index: 9999;',
          },
          xAxis: {
            type: 'value', name: 'DTE',
            nameTextStyle: { color: '#475569', fontSize: 10 },
            axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'Inter' },
            axisLine: { lineStyle: { color: '#1A1A1A' } },
            splitLine: { lineStyle: { color: '#111111' } },
          },
          yAxis: {
            type: 'value', name: 'ATM IV',
            nameTextStyle: { color: '#475569', fontSize: 10 },
            axisLabel: {
              color: '#64748B', fontSize: 10, fontFamily: 'Inter',
              formatter: (v: number) => `${(v*100).toFixed(0)}%`,
            },
            axisLine: { lineStyle: { color: '#1A1A1A' } },
            splitLine: { lineStyle: { color: '#111111' } },
          },
          series: [{
            name: 'ATM IV', type: 'line', smooth: false,
            data: data.map(p => [p.dte, p.atm_iv]),
            lineStyle: { color: '#3B82F6', width: 2 },
            areaStyle: { color: 'rgba(59,130,246,0.08)' },
            itemStyle: { color: '#3B82F6' },
            symbol: 'circle', symbolSize: 5,
            label: {
              show: true, position: 'top',
              color: '#94A3B8', fontSize: 9, fontFamily: 'Inter',
              formatter: (p: any) => `${(p.data[1]*100).toFixed(0)}%`,
            },
          }],
        });
      }
    } catch {}
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(chartEl, null, { renderer: 'canvas' });
    new ResizeObserver(() => chart.resize()).observe(chartEl);
    load();
  });

  $: if (symbol && chart) load();
</script>

<div bind:this={chartEl} class="w-full h-full"></div>
