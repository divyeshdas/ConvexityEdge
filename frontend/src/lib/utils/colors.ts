// Colour scales for heatmaps and Greek visualisations

export function deltaColor(delta: number): string {
  const abs = Math.abs(delta);
  const alpha = Math.min(abs, 1);
  return delta > 0
    ? `rgba(96, 165, 250, ${alpha})`   // blue for positive delta
    : `rgba(248, 113, 113, ${alpha})`; // red for negative delta
}

export function gammaColor(gamma: number): string {
  const clamped = Math.min(gamma * 100, 1);
  return `rgba(52, 211, 153, ${clamped})`;
}

export function vegaColor(vega: number): string {
  const clamped = Math.min(Math.abs(vega) / 50, 1);
  return `rgba(167, 139, 250, ${clamped})`;
}

export function thetaColor(theta: number): string {
  const clamped = Math.min(Math.abs(theta) / 2, 1);
  return `rgba(248, 113, 113, ${clamped})`;
}

// Heatmap gradient stops for ECharts visualMap
export const IV_GRADIENT = [
  { value: 0,   color: '#1E3A5F' },
  { value: 0.2, color: '#1D4ED8' },
  { value: 0.4, color: '#0891B2' },
  { value: 0.6, color: '#D97706' },
  { value: 0.8, color: '#DC2626' },
  { value: 1,   color: '#7C3AED' },
];

export const CHART_COLORS = {
  candleUp:    '#22C55E',
  candleDown:  '#EF4444',
  volume:      '#3B82F6',
  ma20:        '#F59E0B',
  ma50:        '#A78BFA',
  ivOverlay:   '#34D399',
  grid:        '#1A1D27',
  axis:        '#334155',
  crosshair:   '#3B82F6',
  tooltip_bg:  'rgba(30, 34, 46, 0.95)',
  tooltip_border: '#3B82F6',
};
