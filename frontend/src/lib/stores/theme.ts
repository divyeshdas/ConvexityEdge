import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'dark' | 'light';

const DARK_VARS: Record<string, string> = {
  '--t-bg':      '#000000',
  '--t-surface': '#0A0A0A',
  '--t-panel':   '#111111',
  '--t-border':  '#1A1A1A',
  '--t-muted':   '#222222',
  '--t-atm':     '#0C1E33',
};
const LIGHT_VARS: Record<string, string> = {
  '--t-bg':      '#F8F5F0',
  '--t-surface': '#FAF7F3',
  '--t-panel':   '#EEE9E3',
  '--t-border':  '#D4CEC6',
  '--t-muted':   '#C8C1B7',
  '--t-atm':     '#DBEAFE',
};

// IST = UTC+5:30
// Light mode: 09:00–15:30 IST (Indian market hours)
// Dark mode: everything else, or user override
function getISTHour(): number {
  const now = new Date();
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60_000;
  const istMs = utcMs + 5.5 * 3600_000;
  const ist = new Date(istMs);
  return ist.getHours() + ist.getMinutes() / 60;
}

function inferThemeFromIST(): Theme {
  const h = getISTHour();
  return h >= 9 && h < 15.5 ? 'light' : 'dark';
}

function createThemeStore() {
  const stored = browser ? (localStorage.getItem('ce_theme') as Theme | null) : null;
  const initial: Theme = stored ?? inferThemeFromIST();

  const { subscribe, set, update } = writable<Theme>(initial);

  function apply(t: Theme) {
    if (!browser) return;
    const root = document.documentElement;
    root.classList.toggle('dark', t === 'dark');
    const vars = t === 'dark' ? DARK_VARS : LIGHT_VARS;
    for (const [k, v] of Object.entries(vars)) {
      root.style.setProperty(k, v);
    }
    localStorage.setItem('ce_theme', t);
  }

  if (browser) apply(initial);

  return {
    subscribe,
    toggle() {
      update((t) => {
        const next: Theme = t === 'dark' ? 'light' : 'dark';
        apply(next);
        return next;
      });
    },
    setTheme(t: Theme) {
      set(t);
      apply(t);
    },
    // Auto-switch based on IST — call this periodically
    syncToIST() {
      const stored = browser ? localStorage.getItem('ce_theme') : null;
      if (stored) return; // user has an explicit preference
      const inferred = inferThemeFromIST();
      set(inferred);
      apply(inferred);
    },
    clearOverride() {
      if (browser) localStorage.removeItem('ce_theme');
      const inferred = inferThemeFromIST();
      set(inferred);
      apply(inferred);
    },
  };
}

export const theme = createThemeStore();
