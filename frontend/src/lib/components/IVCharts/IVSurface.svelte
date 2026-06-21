<script lang="ts">
  import { onMount } from 'svelte';
  import { ivApi } from '$api/client';

  export let symbol: string;

  let chartEl: HTMLDivElement;
  let chart: any;

  async function load() {
    if (!symbol) return;
    try {
      const data = await ivApi.surface(symbol);
      if (!chart || !data.length) return;

      const strikeSet = [...new Set(data.map(p => p.strike))].sort((a,b)=>a-b);
      const dteSet    = [...new Set(data.map(p => p.dte))].sort((a,b)=>a-b);

      // Build 2D grid
      const map = new Map(data.map(p => [`${p.strike}:${p.dte}`, p.iv_pct]));
      const grid = dteSet.map((dte, di) =>
        strikeSet.map((strike, si) => [si, di, map.get(`${strike}:${dte}`) ?? 0])
      ).flat();

      chart.setOption({
        backgroundColor: '#000000',
        animation: false,
        tooltip: {},
        visualMap: {
          min: 0, max: 100, dimension: 2,
          inRange: { color: ['#1E3A5F','#3B82F6','#F59E0B','#EF4444'] },
          textStyle: { color: '#64748B', fontSize: 9 },
        },
        xAxis3D: {
          type: 'category', data: strikeSet,
          name: 'Strike', nameTextStyle: { color: '#64748B' },
          axisLabel: { color: '#475569', fontSize: 9 },
        },
        yAxis3D: {
          type: 'category', data: dteSet,
          name: 'DTE', nameTextStyle: { color: '#64748B' },
          axisLabel: { color: '#475569', fontSize: 9 },
        },
        zAxis3D: {
          type: 'value', name: 'IV %',
          nameTextStyle: { color: '#64748B' },
          axisLabel: { color: '#475569', fontSize: 9 },
        },
        grid3D: {
          boxWidth: 200, boxDepth: 80,
          light: { main: { intensity: 1.2 }, ambient: { intensity: 0.3 } },
          viewControl: { autoRotate: false, alpha: 30, beta: 40 },
          axisLine: { lineStyle: { color: '#1A1A1A' } },
          splitLine: { lineStyle: { color: '#111111' } },
        },
        series: [{
          type: 'surface',
          data: grid,
          shading: 'color',
          itemStyle: { opacity: 0.85 },
        }],
      });
    } catch {}
  }

  onMount(async () => {
    // ECharts GL for 3D surface
    const echarts = await import('echarts');
    await import('echarts-gl');
    chart = echarts.init(chartEl, null, { renderer: 'webgl' as any });
    new ResizeObserver(() => chart.resize()).observe(chartEl);
    load();
  });

  $: if (symbol && chart) load();
</script>

<div bind:this={chartEl} class="w-full h-full"></div>
