// Number formatting utilities for trading terminal display

export function fmtPrice(v: number | null | undefined, decimals = 2): string {
  if (v == null || isNaN(v)) return '—';
  return v.toFixed(decimals);
}

export function fmtPct(v: number | null | undefined, decimals = 1): string {
  if (v == null || isNaN(v)) return '—';
  return `${(v * 100).toFixed(decimals)}%`;
}

export function fmtGreek(v: number | null | undefined, decimals = 3): string {
  if (v == null || isNaN(v)) return '—';
  return v.toFixed(decimals);
}

export function fmtVolume(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '—';
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000)     return `${(v / 1_000).toFixed(1)}K`;
  return v.toString();
}

export function fmtChange(v: number | null | undefined, decimals = 2): string {
  if (v == null || isNaN(v)) return '—';
  const sign = v >= 0 ? '+' : '';
  return `${sign}${v.toFixed(decimals)}`;
}

export function fmtChangePct(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '—';
  const sign = v >= 0 ? '+' : '';
  return `${sign}${(v * 100).toFixed(2)}%`;
}

export function fmtDTE(dte: number): string {
  if (dte <= 0) return 'Expired';
  if (dte === 1) return '1d';
  if (dte < 30)  return `${dte}d`;
  const weeks = Math.round(dte / 7);
  return `${weeks}w`;
}

export function fmtDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
}

export function fmtExpiryLabel(dateStr: string, dte: number): string {
  return `${fmtDate(dateStr)} · ${fmtDTE(dte)}`;
}

export function fmtCurrency(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(v);
}

export function signClass(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return 'num-neutral';
  if (v > 0) return 'num-positive';
  if (v < 0) return 'num-negative';
  return 'num-neutral';
}

export function ivColor(iv: number): string {
  // Low IV = blue, mid = yellow, high = red
  if (iv < 0.2) return '#60A5FA';
  if (iv < 0.4) return '#FBBF24';
  if (iv < 0.6) return '#F97316';
  return '#EF4444';
}
