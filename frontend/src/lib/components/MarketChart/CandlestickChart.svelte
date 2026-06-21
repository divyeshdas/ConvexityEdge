<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { marketApi } from '$api/client';
  import { CHART_COLORS } from '$utils/colors';
  import { theme } from '$stores/theme';
  import type { OHLCBar } from '$api/types';

  export let symbol: string;

  let wrapperEl: HTMLDivElement;
  let chartEl: HTMLDivElement;
  let chart: any;
  let bars: OHLCBar[] = [];
  let loading = true;

  const PERIODS = ['1mo','3mo','6mo','1y'];
  let period = '3mo';

  async function loadData() {
    loading = true;
    try {
      bars = await marketApi.chart(symbol, period, '1d');
      renderChart();
    } catch (e) {
      console.error('Chart load failed', e);
    } finally {
      loading = false;
    }
  }

  function renderChart() {
    if (!chart || !bars.length) return;

    chart.resize();

    const dates   = bars.map(b => new Date(b.time * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    const ohlc    = bars.map(b => [b.open, b.close, b.low, b.high]);
    const volumes = bars.map(b => b.volume);

    const ma20 = bars.map((_, i) => {
      if (i < 19) return null;
      const slice = bars.slice(i - 19, i + 1);
      return slice.reduce((s, b) => s + b.close, 0) / 20;
    });

    const ma50 = bars.map((_, i) => {
      if (i < 49) return null;
      const slice = bars.slice(i - 49, i + 1);
      return slice.reduce((s, b) => s + b.close, 0) / 50;
    });

    const isDark = $theme === 'dark';
    chart.setOption({
      backgroundColor: isDark ? '#0D0F14' : '#F1F4F9',
      animation: false,
      grid: [
        { left: 60, right: 60, top: 10, bottom: 80 },
        { left: 60, right: 60, top: '70%', bottom: 30 },
      ],
      xAxis: [
        {
          type: 'category', data: dates, gridIndex: 0,
          axisLine: { lineStyle: { color: CHART_COLORS.axis } },
          axisLabel: { show: false },
          splitLine: { lineStyle: { color: CHART_COLORS.grid } },
        },
        {
          type: 'category', data: dates, gridIndex: 1,
          axisLine: { lineStyle: { color: CHART_COLORS.axis } },
          axisLabel: { color: '#475569', fontSize: 10, fontFamily: 'Inter' },
          splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          gridIndex: 0, scale: true,
          axisLine: { lineStyle: { color: CHART_COLORS.axis } },
          axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'Inter' },
          splitLine: { lineStyle: { color: CHART_COLORS.grid } },
        },
        {
          gridIndex: 1, scale: true,
          axisLine: { lineStyle: { color: CHART_COLORS.axis } },
          axisLabel: { color: '#64748B', fontSize: 9, fontFamily: 'Inter' },
          splitLine: { show: false },
        },
      ],
      tooltip: {
        trigger: 'axis',
        confine: true,
        appendToBody: true,
        axisPointer: { type: 'cross', crossStyle: { color: CHART_COLORS.crosshair } },
        backgroundColor: CHART_COLORS.tooltip_bg,
        borderColor: CHART_COLORS.tooltip_border,
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#CBD5E1', fontSize: 11, fontFamily: 'Inter' },
        extraCssText: 'border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); z-index: 9999;',
      },
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
        {
          type: 'slider', xAxisIndex: [0, 1], bottom: 0, height: 20,
          fillerColor: 'rgba(59,130,246,0.1)', borderColor: '#252836',
          textStyle: { color: '#475569' },
        },
      ],
      series: [
        {
          name: symbol, type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0,
          data: ohlc,
          itemStyle: {
            color: CHART_COLORS.candleUp, color0: CHART_COLORS.candleDown,
            borderColor: CHART_COLORS.candleUp, borderColor0: CHART_COLORS.candleDown,
          },
        },
        {
          name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
          data: ma20, smooth: true,
          lineStyle: { color: CHART_COLORS.ma20, width: 1 },
          symbol: 'none', connectNulls: true,
        },
        {
          name: 'MA50', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
          data: ma50, smooth: true,
          lineStyle: { color: CHART_COLORS.ma50, width: 1 },
          symbol: 'none', connectNulls: true,
        },
        {
          name: 'Volume', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
          data: volumes,
          itemStyle: {
            color: (params: any) => {
              const b = bars[params.dataIndex];
              return b.close >= b.open ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)';
            },
          },
        },
      ],
    }, true);
  }

  onMount(() => {
    let ro: ResizeObserver;
    (async () => {
      const echarts = await import('echarts');
      await new Promise<void>(r => requestAnimationFrame(() => r()));

      const w = wrapperEl.clientWidth;
      const h = wrapperEl.clientHeight;
      chart = echarts.init(chartEl, null, { renderer: 'canvas', width: w, height: h });

      ro = new ResizeObserver(() => {
        const rw = wrapperEl.clientWidth;
        const rh = wrapperEl.clientHeight;
        if (rw > 0 && rh > 0) chart.resize({ width: rw, height: rh });
      });
      ro.observe(wrapperEl);
      await loadData();
    })();
    return () => { if (ro) ro.disconnect(); if (chart) chart.dispose(); };
  });

  $: if (browser && symbol) loadData();
  $: if (browser && period && chart) loadData();
  $: if (browser && $theme && chart) renderChart();
</script>

<div style="display: flex; flex-direction: column; height: 100%; background: var(--color-terminal-bg, #0D0F14);">
  <!-- Chart toolbar -->
  <div class="flex items-center gap-2 px-3 py-1 border-b border-terminal-border" style="flex-shrink: 0;">
    <span class="text-slate-300 text-xs font-mono font-semibold">{symbol}</span>
    <span class="text-neutral text-xxs">Daily</span>
    <div class="flex-1"></div>
    <div class="flex items-center gap-1">
      {#each PERIODS as p}
        <button
          class="px-2 py-0.5 text-xxs font-mono border transition-colors
            {period === p
              ? 'border-accent text-accent bg-accent/10'
              : 'border-terminal-border text-neutral hover:border-slate-500'}"
          on:click={() => period = p}
        >{p}</button>
      {/each}
    </div>
    <div class="flex items-center gap-3 ml-2">
      <span class="flex items-center gap-1 text-xxs" style="color:#F59E0B">
        <span class="w-4 h-px" style="background:#F59E0B;display:inline-block"></span>MA20
      </span>
      <span class="flex items-center gap-1 text-xxs" style="color:#A78BFA">
        <span class="w-4 h-px" style="background:#A78BFA;display:inline-block"></span>MA50
      </span>
    </div>
  </div>

  <!-- Chart canvas -->
  <div bind:this={wrapperEl} style="flex: 1; position: relative; overflow: hidden; min-height: 0;">
    {#if loading}
      <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 10; background: var(--color-terminal-bg, #0D0F14);">
        <svg class="w-5 h-5 animate-spin text-accent" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>
    {/if}
    <div bind:this={chartEl} style="width: 100%; height: 100%;"></div>
  </div>
</div>
