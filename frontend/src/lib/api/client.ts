import type {
  Quote, Expiry, OHLCBar,
  OptionChain, BSPricingRequest, BSPricingResult,
  IVSmilePoint, IVTermPoint, IVSurfacePoint,
  StrategyLeg, StrategyResult,
  TradeAnalysisRequest, TradeAnalysisResult,
  DashboardAnalytics, SymbolSearchResult,
} from './types';

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Symbols ────────────────────────────────────────────────────────────────
export const symbolsApi = {
  search: (q: string) =>
    request<SymbolSearchResult[]>(`/symbols/search?q=${encodeURIComponent(q)}`),
};

// ── Market ─────────────────────────────────────────────────────────────────
export const marketApi = {
  quote:   (symbol: string) => request<Quote>(`/market/quote/${symbol}`),
  chart:   (symbol: string, period = '3mo', interval = '1d') =>
    request<OHLCBar[]>(`/market/chart/${symbol}?period=${period}&interval=${interval}`),
  expiries: (symbol: string) => request<Expiry[]>(`/options/expiries/${symbol}`),
};

// ── Options Chain ──────────────────────────────────────────────────────────
export const optionsApi = {
  chain: (symbol: string, expiry: string, strikes = 30) =>
    request<OptionChain>(`/options/chain/${symbol}?expiry=${expiry}&strikes=${strikes}`),
};

// ── Pricing ────────────────────────────────────────────────────────────────
export const pricingApi = {
  blackScholes: (body: BSPricingRequest) =>
    request<BSPricingResult>('/pricing/black-scholes', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

// ── IV ────────────────────────────────────────────────────────────────────
export const ivApi = {
  smile:         (symbol: string, expiry: string) =>
    request<IVSmilePoint[]>(`/iv/smile/${symbol}?expiry=${expiry}`),
  termStructure: (symbol: string) =>
    request<IVTermPoint[]>(`/iv/term-structure/${symbol}`),
  surface:       (symbol: string) =>
    request<IVSurfacePoint[]>(`/iv/surface/${symbol}`),
  skew:          (symbol: string, expiry: string) =>
    request<IVSmilePoint[]>(`/iv/skew/${symbol}?expiry=${expiry}`),
};

// ── Strategy ──────────────────────────────────────────────────────────────
export const strategyApi = {
  build: (strategy_name: string, symbol: string, expiry: string, underlying_price: number) =>
    request<{ legs: StrategyLeg[] }>('/strategy/build', {
      method: 'POST',
      body: JSON.stringify({ strategy_name, symbol, expiry, underlying_price }),
    }),
  payoff: (legs: StrategyLeg[], price_range?: [number, number]) =>
    request<StrategyResult>('/strategy/payoff', {
      method: 'POST',
      body: JSON.stringify({ legs, price_range }),
    }),
  templates: () => request<{ name: string; description: string }[]>('/strategy/templates'),
};

// ── Trade Analysis ─────────────────────────────────────────────────────────
export const tradeApi = {
  analyze: (body: TradeAnalysisRequest) =>
    request<TradeAnalysisResult>('/trade/analyze', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

// ── Dashboard ──────────────────────────────────────────────────────────────
export const dashboardApi = {
  analytics: (symbol: string) =>
    request<DashboardAnalytics>(`/dashboard/analytics/${symbol}`),
};
