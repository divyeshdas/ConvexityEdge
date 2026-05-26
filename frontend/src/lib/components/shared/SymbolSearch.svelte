<script lang="ts">
  import { selectedSymbol } from '$stores/market';
  import { symbolsApi } from '$api/client';
  import type { SymbolSearchResult } from '$api/types';

  let query = $selectedSymbol;
  let results: SymbolSearchResult[] = [];
  let open = false;
  let debounceTimer: ReturnType<typeof setTimeout>;

  function onInput() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      if (query.length >= 1) {
        try {
          results = await symbolsApi.search(query);
          open = results.length > 0;
        } catch {
          results = [];
        }
      } else {
        results = [];
        open = false;
      }
    }, 250);
  }

  function select(sym: SymbolSearchResult) {
    selectedSymbol.set(sym.ticker);
    query = sym.ticker;
    open = false;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') open = false;
    if (e.key === 'Enter' && results.length > 0) select(results[0]);
  }

  function onBlur() {
    setTimeout(() => (open = false), 150);
  }
</script>

<div class="relative">
  <input
    class="bg-terminal-bg border border-terminal-border text-slate-200 font-mono text-xs
           px-2 py-1 w-24 outline-none focus:border-accent focus:w-32 transition-all uppercase"
    bind:value={query}
    on:input={onInput}
    on:keydown={onKeydown}
    on:blur={onBlur}
    placeholder="Symbol"
    autocomplete="off"
    spellcheck="false"
  />

  {#if open}
    <div class="absolute top-full left-0 mt-1 w-56 bg-terminal-panel border border-terminal-border z-50 shadow-xl animate-fade-in">
      {#each results as r}
        <button
          class="w-full flex items-center gap-2 px-3 py-2 hover:bg-terminal-muted text-left border-b border-terminal-border last:border-0"
          on:mousedown|preventDefault={() => select(r)}
        >
          <span class="font-mono text-xs text-accent font-bold w-16 shrink-0">{r.ticker}</span>
          <span class="text-slate-400 text-xxs truncate">{r.name}</span>
          <span class="text-neutral text-xxs ml-auto shrink-0">{r.exchange}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>
