import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const INTERVAL_MS = 60_000;

export const refreshTick  = writable<number>(0);
export const nextRefreshIn = writable<number>(INTERVAL_MS / 1000);

let _countdownHandle: ReturnType<typeof setInterval> | null = null;
let _refreshHandle:   ReturnType<typeof setInterval> | null = null;

export function startRefreshTimer(onTick: () => void) {
  if (!browser) return;
  stopRefreshTimer();

  let remaining = INTERVAL_MS / 1000;

  _countdownHandle = setInterval(() => {
    remaining -= 1;
    nextRefreshIn.set(remaining);
    if (remaining <= 0) remaining = INTERVAL_MS / 1000;
  }, 1000);

  _refreshHandle = setInterval(() => {
    refreshTick.update((n) => n + 1);
    onTick();
    remaining = INTERVAL_MS / 1000;
  }, INTERVAL_MS);
}

export function stopRefreshTimer() {
  if (_countdownHandle) clearInterval(_countdownHandle);
  if (_refreshHandle)   clearInterval(_refreshHandle);
  _countdownHandle = null;
  _refreshHandle   = null;
}
