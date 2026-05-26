-- Seed default symbols
INSERT INTO symbols (ticker, name, exchange, asset_type) VALUES
    ('AAPL',  'Apple Inc.',                       'NASDAQ', 'equity'),
    ('MSFT',  'Microsoft Corporation',             'NASDAQ', 'equity'),
    ('AMZN',  'Amazon.com Inc.',                   'NASDAQ', 'equity'),
    ('NVDA',  'NVIDIA Corporation',                'NASDAQ', 'equity'),
    ('GOOGL', 'Alphabet Inc.',                     'NASDAQ', 'equity'),
    ('META',  'Meta Platforms Inc.',               'NASDAQ', 'equity'),
    ('TSLA',  'Tesla Inc.',                        'NASDAQ', 'equity'),
    ('SPY',   'SPDR S&P 500 ETF Trust',            'NYSE',   'etf'),
    ('QQQ',   'Invesco QQQ Trust',                 'NASDAQ', 'etf'),
    ('IWM',   'iShares Russell 2000 ETF',          'NYSE',   'etf'),
    ('GLD',   'SPDR Gold Shares',                  'NYSE',   'etf'),
    ('TLT',   'iShares 20+ Year Treasury Bond ETF','NASDAQ', 'etf')
ON CONFLICT (ticker) DO NOTHING;

-- Seed strategy definitions
INSERT INTO strategy_definitions (name, description) VALUES
    ('Long Call',       'Buy a call option. Bullish, limited risk, unlimited upside.'),
    ('Long Put',        'Buy a put option. Bearish, limited risk, upside capped at strike.'),
    ('Covered Call',    'Hold stock, sell OTM call. Income strategy, caps upside.'),
    ('Protective Put',  'Hold stock, buy OTM put. Insurance against downside.'),
    ('Bull Call Spread','Buy lower-strike call, sell higher-strike call. Capped bullish.'),
    ('Bear Put Spread', 'Buy higher-strike put, sell lower-strike put. Capped bearish.'),
    ('Straddle',        'Buy ATM call and put with same strike/expiry. Volatility play.'),
    ('Strangle',        'Buy OTM call and OTM put. Cheaper vol play than straddle.'),
    ('Iron Condor',     'Sell OTM strangle, buy further OTM strangle. Range-bound income.')
ON CONFLICT DO NOTHING;
