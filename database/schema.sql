-- ConvexityEdge — PostgreSQL Schema
-- All timestamps are stored as UTC

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Symbols ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS symbols (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(20)  UNIQUE NOT NULL,
    name        VARCHAR(200),
    exchange    VARCHAR(20),
    asset_type  VARCHAR(20)  DEFAULT 'equity',
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Option Contracts ──────────────────────────────────────────────────────────
-- One row per unique (symbol, type, strike, expiry) tuple
CREATE TABLE IF NOT EXISTS option_contracts (
    id          SERIAL PRIMARY KEY,
    symbol_id   INTEGER      NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    option_type CHAR(1)      NOT NULL CHECK (option_type IN ('C','P')),
    strike      NUMERIC(12,4) NOT NULL,
    expiry      DATE          NOT NULL,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (symbol_id, option_type, strike, expiry)
);

CREATE INDEX IF NOT EXISTS idx_contracts_symbol ON option_contracts(symbol_id);
CREATE INDEX IF NOT EXISTS idx_contracts_expiry  ON option_contracts(expiry);
CREATE INDEX IF NOT EXISTS idx_contracts_strike  ON option_contracts(strike);

-- ── Option Chain Snapshots ────────────────────────────────────────────────────
-- Time-series of market data written every 60 seconds
CREATE TABLE IF NOT EXISTS option_chain_snapshots (
    id               BIGSERIAL    PRIMARY KEY,
    contract_id      INTEGER      NOT NULL REFERENCES option_contracts(id) ON DELETE CASCADE,
    snapshot_time    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    underlying_price NUMERIC(12,4),
    bid              NUMERIC(12,4),
    ask              NUMERIC(12,4),
    last_price       NUMERIC(12,4),
    volume           INTEGER      DEFAULT 0,
    open_interest    INTEGER      DEFAULT 0,
    implied_vol      NUMERIC(8,6),
    delta            NUMERIC(8,6),
    gamma            NUMERIC(10,8),
    vega             NUMERIC(10,6),
    theta            NUMERIC(10,6),
    rho              NUMERIC(10,6),
    iv_change_1d     NUMERIC(8,6)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_contract_time
    ON option_chain_snapshots(contract_id, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_time
    ON option_chain_snapshots(snapshot_time DESC);

-- ── IV History ────────────────────────────────────────────────────────────────
-- Rolled-up IV observations for term-structure and smile analytics
CREATE TABLE IF NOT EXISTS iv_history (
    id               BIGSERIAL    PRIMARY KEY,
    symbol_id        INTEGER      NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    expiry           DATE         NOT NULL,
    strike           NUMERIC(12,4) NOT NULL,
    option_type      CHAR(1)      NOT NULL CHECK (option_type IN ('C','P')),
    recorded_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    implied_vol      NUMERIC(8,6),
    underlying_price NUMERIC(12,4)
);

CREATE INDEX IF NOT EXISTS idx_iv_history_symbol_expiry
    ON iv_history(symbol_id, expiry, recorded_at DESC);

-- ── Strategy Definitions ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategy_definitions (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ── Strategy Legs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategy_legs (
    id              SERIAL      PRIMARY KEY,
    strategy_def_id INTEGER     REFERENCES strategy_definitions(id) ON DELETE SET NULL,
    session_id      UUID        NOT NULL DEFAULT uuid_generate_v4(),
    option_type     CHAR(1)     CHECK (option_type IN ('C','P')),
    strike          NUMERIC(12,4),
    expiry          DATE,
    action          VARCHAR(4)  CHECK (action IN ('BUY','SELL')),
    quantity        INTEGER     DEFAULT 1,
    premium         NUMERIC(12,4),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legs_session ON strategy_legs(session_id);

-- ── Trade Analysis Results ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trade_analysis_results (
    id          SERIAL      PRIMARY KEY,
    symbol      VARCHAR(20) NOT NULL,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    params      JSONB       NOT NULL,
    results     JSONB       NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_results_symbol_time
    ON trade_analysis_results(symbol, analyzed_at DESC);
