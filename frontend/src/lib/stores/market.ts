import { writable, derived } from 'svelte/store';
import type { OptionChain, Quote, Expiry } from '$lib/api/types';

export const selectedSymbol = writable<string>('SPY');
export const selectedExpiry  = writable<string>('');
export const strikeCount     = writable<number>(20);

export const quote       = writable<Quote | null>(null);
export const optionChain = writable<OptionChain | null>(null);
export const expiries    = writable<Expiry[]>([]);

export const lastUpdated  = writable<Date | null>(null);
export const isLoading    = writable<boolean>(false);
export const isStale      = writable<boolean>(false);

// ATM strike derived from chain + quote
export const atmStrike = derived(
  [optionChain, quote],
  ([$chain, $quote]) => {
    if (!$chain || !$quote) return null;
    const strikes = $chain.strikes.map((s) => s.strike);
    if (!strikes.length) return null;
    return strikes.reduce((prev, curr) =>
      Math.abs(curr - $quote.price) < Math.abs(prev - $quote.price) ? curr : prev
    );
  }
);
