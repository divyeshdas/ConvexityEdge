// ── Market ─────────────────────────────────────────────────────────────────
export interface Quote {
  symbol:           string;
  price:            number;
  change:           number;
  change_pct:       number;
  volume:           number;
  market_cap:       number | null;
  timestamp:        string;
}

export interface Expiry {
  date:     string;   // ISO date string "YYYY-MM-DD"
  dte:      number;   // days to expiry
  label:    string;   // "Jun 20 '25 · 25d"
}

export interface OHLCBar {
  time:   number;  // unix timestamp
  open:   number;
  high:   number;
  low:    number;
  close:  number;
  volume: number;
}

// ── Options Chain ──────────────────────────────────────────────────────────
export interface Greeks {
  delta: number;
  gamma: number;
  vega:  number;
  theta: number;
  rho:   number;
}

export interface OptionLeg {
  option_type:   'C' | 'P';
  strike:        number;
  expiry:        string;
  bid:           number;
  ask:           number;
  last:          number;
  volume:        number;
  open_interest: number;
  implied_vol:   number;
  iv_change_1d:  number | null;
  greeks:        Greeks;
  in_the_money:  boolean;
}

export interface ChainStrike {
  strike:  number;
  call:    OptionLeg | null;
  put:     OptionLeg | null;
  is_atm:  boolean;
}

export interface ChainStats {
  atm_iv:          number;
  hist_vol_30d:    number;
  pcr_volume:      number;
  pcr_oi:          number;
  total_call_vol:  number;
  total_put_vol:   number;
  total_call_oi:   number;
  total_put_oi:    number;
  iv_change_avg:   number;
}

export interface OptionChain {
  symbol:       string;
  expiry:       string;
  dte:          number;
  underlying:   number;
  strikes:      ChainStrike[];
  stats:        ChainStats;
  fetched_at:   string;
}

// ── Pricing ────────────────────────────────────────────────────────────────
export interface BSPricingRequest {
  S:           number;
  K:           number;
  T:           number;
  r:           number;
  q:           number;
  sigma:       number;
  option_type: 'C' | 'P';
}

export interface BSPricingResult {
  price:           number;
  intrinsic_value: number;
  time_value:      number;
  greeks:          Greeks;
  d1:              number;
  d2:              number;
}

// ── Implied Volatility ─────────────────────────────────────────────────────
export interface IVSmilePoint {
  strike:       number;
  iv:           number;
  moneyness:    number;  // ln(K/S)
  option_type:  'C' | 'P';
}

export interface IVTermPoint {
  expiry:     string;
  dte:        number;
  atm_iv:     number;
}

export interface IVSurfacePoint {
  strike:     number;
  dte:        number;
  iv:         number;
  moneyness:  number;
}

// ── Strategy ──────────────────────────────────────────────────────────────
export interface StrategyLeg {
  option_type: 'C' | 'P';
  strike:      number;
  expiry:      string;
  action:      'BUY' | 'SELL';
  quantity:    number;
  premium:     number;
}

export interface StrategyResult {
  net_premium:     number;
  max_profit:      number | null;  // null = unlimited
  max_loss:        number | null;
  break_evens:     number[];
  risk_reward:     number | null;
  expected_move:   number;
  payoff_curve:    { price: number; pnl: number }[];
}

// ── Trade Analysis ─────────────────────────────────────────────────────────
export interface TradeAnalysisRequest {
  symbol:          string;
  entry_price:     number;
  implied_vol:     number;
  expiry:          string;
  preset_levels:   number;
  initial_size:    number;
  subsequent_size: number;
  vol_floor:       'daily' | 'weekly' | 'monthly';
}

export interface TradeAnalysisResult {
  floor_value:        number;
  max_cash_allocation: number;
  profit_per_level:   number;
  all_level_profit:   number;
  expected_move:      number;
  risk_reward:        number;
}

// ── Dashboard ──────────────────────────────────────────────────────────────
export interface DashboardAnalytics {
  symbol:           string;
  atm_iv:           number;
  iv_rank:          number;
  hist_vol_30d:     number;
  iv_hv_spread:     number;
  pcr_volume:       number;
  pcr_oi:           number;
  total_volume:     number;
  top_volume_calls: { strike: number; volume: number }[];
  top_volume_puts:  { strike: number; volume: number }[];
  top_oi_calls:     { strike: number; oi: number }[];
  top_oi_puts:      { strike: number; oi: number }[];
  greeks_exposure:  {
    net_delta: number;
    net_gamma: number;
    net_vega:  number;
    net_theta: number;
  };
}

// ── Symbol ────────────────────────────────────────────────────────────────
export interface SymbolSearchResult {
  ticker:     string;
  name:       string;
  exchange:   string;
  asset_type: string;
}
