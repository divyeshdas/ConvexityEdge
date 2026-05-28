<script lang="ts">
  import { selectedSymbol } from '$stores/market';

  const INDICES = [
    { ticker: 'NIFTY',      name: 'Nifty 50',               sector: 'Index' },
    { ticker: 'BANKNIFTY',  name: 'Bank Nifty',             sector: 'Index' },
    { ticker: 'FINNIFTY',   name: 'Fin. Services Nifty',    sector: 'Index' },
    { ticker: 'MIDCPNIFTY', name: 'Midcap Select Nifty',    sector: 'Index' },
    { ticker: 'SENSEX',     name: 'BSE Sensex',             sector: 'Index' },
  ];

  const STOCKS = [
    { ticker: 'RELIANCE',   name: 'Reliance Industries',    sector: 'Energy' },
    { ticker: 'TCS',        name: 'Tata Consultancy',       sector: 'IT' },
    { ticker: 'INFY',       name: 'Infosys',                sector: 'IT' },
    { ticker: 'HDFCBANK',   name: 'HDFC Bank',              sector: 'Banking' },
    { ticker: 'ICICIBANK',  name: 'ICICI Bank',             sector: 'Banking' },
    { ticker: 'SBIN',       name: 'State Bank of India',    sector: 'Banking' },
    { ticker: 'AXISBANK',   name: 'Axis Bank',              sector: 'Banking' },
    { ticker: 'KOTAKBANK',  name: 'Kotak Mahindra Bank',    sector: 'Banking' },
    { ticker: 'BAJFINANCE', name: 'Bajaj Finance',          sector: 'Finance' },
    { ticker: 'BAJAJFINSV', name: 'Bajaj Finserv',          sector: 'Finance' },
    { ticker: 'HCLTECH',    name: 'HCL Technologies',       sector: 'IT' },
    { ticker: 'WIPRO',      name: 'Wipro',                  sector: 'IT' },
    { ticker: 'TECHM',      name: 'Tech Mahindra',          sector: 'IT' },
    { ticker: 'LTIM',       name: 'LTIMindtree',            sector: 'IT' },
    { ticker: 'ITC',        name: 'ITC',                    sector: 'FMCG' },
    { ticker: 'HINDUNILVR', name: 'Hindustan Unilever',     sector: 'FMCG' },
    { ticker: 'NESTLEIND',  name: 'Nestle India',           sector: 'FMCG' },
    { ticker: 'ASIANPAINT', name: 'Asian Paints',           sector: 'Paints' },
    { ticker: 'MARUTI',     name: 'Maruti Suzuki',          sector: 'Auto' },
    { ticker: 'TATAMOTORS', name: 'Tata Motors',            sector: 'Auto' },
    { ticker: 'TITAN',      name: 'Titan Company',          sector: 'Consumer' },
    { ticker: 'SUNPHARMA',  name: 'Sun Pharma',             sector: 'Pharma' },
    { ticker: 'ONGC',       name: 'ONGC',                   sector: 'Energy' },
    { ticker: 'NTPC',       name: 'NTPC',                   sector: 'Power' },
    { ticker: 'POWERGRID',  name: 'Power Grid Corp',        sector: 'Power' },
    { ticker: 'TATASTEEL',  name: 'Tata Steel',             sector: 'Metals' },
    { ticker: 'JSWSTEEL',   name: 'JSW Steel',              sector: 'Metals' },
    { ticker: 'ADANIENT',   name: 'Adani Enterprises',      sector: 'Conglom.' },
    { ticker: 'ADANIPORTS', name: 'Adani Ports & SEZ',      sector: 'Logistics' },
    { ticker: 'ULTRACEMCO', name: 'UltraTech Cement',       sector: 'Cement' },
  ];

  const SECTOR_COLORS: Record<string, string> = {
    'Index':    'text-blue-400 bg-blue-400/10',
    'Banking':  'text-emerald-400 bg-emerald-400/10',
    'IT':       'text-violet-400 bg-violet-400/10',
    'Finance':  'text-cyan-400 bg-cyan-400/10',
    'FMCG':     'text-amber-400 bg-amber-400/10',
    'Energy':   'text-orange-400 bg-orange-400/10',
    'Auto':     'text-rose-400 bg-rose-400/10',
    'Pharma':   'text-teal-400 bg-teal-400/10',
    'Metals':   'text-slate-300 bg-slate-400/10',
    'Power':    'text-yellow-400 bg-yellow-400/10',
    'Cement':   'text-stone-400 bg-stone-400/10',
    'Paints':   'text-pink-400 bg-pink-400/10',
    'Consumer': 'text-indigo-400 bg-indigo-400/10',
    'Conglom.': 'text-lime-400 bg-lime-400/10',
    'Logistics':'text-sky-400 bg-sky-400/10',
  };

  let query = '';
  let open = false;
  let inputEl: HTMLInputElement;

  $: showIndices = !query || 'index'.includes(query.toLowerCase())
    || INDICES.some(i => i.ticker.includes(query.toUpperCase()) || i.name.toUpperCase().includes(query.toUpperCase()));

  $: filteredIndices = query
    ? INDICES.filter(s =>
        s.ticker.includes(query.toUpperCase()) ||
        s.name.toUpperCase().includes(query.toUpperCase())
      )
    : INDICES;

  $: filteredStocks = query
    ? STOCKS.filter(s =>
        s.ticker.includes(query.toUpperCase()) ||
        s.name.toUpperCase().includes(query.toUpperCase()) ||
        s.sector.toUpperCase().includes(query.toUpperCase())
      )
    : STOCKS;

  function select(ticker: string) {
    selectedSymbol.set(ticker);
    query = '';
    open = false;
  }

  function openDropdown() {
    open = true;
    query = '';
    setTimeout(() => inputEl?.focus(), 10);
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') { open = false; query = ''; }
    if (e.key === 'Enter') {
      const first = filteredIndices[0] ?? filteredStocks[0];
      if (first) select(first.ticker);
    }
  }

  function onBlur() {
    setTimeout(() => { open = false; query = ''; }, 160);
  }
</script>

<div class="relative">
  <!-- Trigger button — shows current symbol -->
  {#if !open}
    <button
      on:click={openDropdown}
      class="flex items-center gap-1.5 px-2.5 py-1 bg-terminal-bg border border-terminal-border
             hover:border-accent/60 hover:bg-terminal-panel transition-all group"
    >
      <span class="font-mono font-semibold text-xs text-accent tracking-wide">
        {$selectedSymbol || 'Select'}
      </span>
      <svg class="w-3 h-3 text-neutral group-hover:text-slate-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </button>
  {:else}
    <!-- Search input — visible when open -->
    <input
      bind:this={inputEl}
      bind:value={query}
      on:keydown={onKeydown}
      on:blur={onBlur}
      placeholder="Search symbol or company..."
      autocomplete="off"
      spellcheck="false"
      class="px-2.5 py-1 bg-terminal-bg border border-accent text-slate-200 text-xs
             outline-none w-44 placeholder-neutral/60"
    />
  {/if}

  <!-- Dropdown panel -->
  {#if open}
    <div class="absolute top-full left-0 mt-1 w-72 bg-terminal-panel border border-terminal-border
                z-50 shadow-2xl animate-fade-in overflow-hidden"
         style="max-height: 400px; overflow-y: auto;">

      {#if filteredIndices.length > 0}
        <div class="px-3 pt-2.5 pb-1">
          <span class="text-neutral/70 text-xxs font-medium uppercase tracking-wider">Indices</span>
        </div>
        {#each filteredIndices as item}
          <button
            class="w-full flex items-center gap-2 px-3 py-2 hover:bg-terminal-muted transition-colors text-left"
            on:mousedown|preventDefault={() => select(item.ticker)}
          >
            <span class="font-mono font-bold text-xs text-accent w-[88px] shrink-0">{item.ticker}</span>
            <span class="text-slate-300 text-xs flex-1 truncate">{item.name}</span>
            <span class="text-xxs px-1.5 py-0.5 rounded {SECTOR_COLORS[item.sector] ?? 'text-neutral bg-neutral/10'} shrink-0">
              {item.sector}
            </span>
          </button>
        {/each}
      {/if}

      {#if filteredStocks.length > 0}
        <div class="px-3 pt-2.5 pb-1 {filteredIndices.length > 0 ? 'border-t border-terminal-border mt-1' : ''}">
          <span class="text-neutral/70 text-xxs font-medium uppercase tracking-wider">NSE F&amp;O Stocks</span>
        </div>
        {#each filteredStocks as item}
          <button
            class="w-full flex items-center gap-2 px-3 py-2 hover:bg-terminal-muted transition-colors text-left"
            on:mousedown|preventDefault={() => select(item.ticker)}
          >
            <span class="font-mono font-bold text-xs text-accent w-[88px] shrink-0">{item.ticker}</span>
            <span class="text-slate-300 text-xs flex-1 truncate">{item.name}</span>
            <span class="text-xxs px-1.5 py-0.5 rounded {SECTOR_COLORS[item.sector] ?? 'text-neutral bg-neutral/10'} shrink-0">
              {item.sector}
            </span>
          </button>
        {/each}
      {/if}

      {#if filteredIndices.length === 0 && filteredStocks.length === 0}
        <div class="px-3 py-4 text-neutral text-xs text-center">No results for "{query}"</div>
      {/if}
    </div>
  {/if}
</div>
