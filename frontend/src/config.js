// In development the Vite dev server proxies backend HTTP routes, so API calls
// must use a relative base (empty string). This keeps the browser on
// localhost:3000 and avoids CORS, even if VITE_API_URL/REACT_API_BASE_URL is
// present in the shell or env files.
const DEV_API_BASE_URL = '';

// In production, the browser must call the backend directly.
const PROD_API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.REACT_API_BASE_URL ||
  'http://localhost:8000';

// In development the Vite dev server proxies /data, /api, /health to the
// backend, so API calls must use a relative base (empty string) — the browser
// sends them to localhost:3000 and Vite forwards them upstream, avoiding CORS.
// In a production build import.meta.env.DEV is false, so the full backend URL
// from REACT_API_BASE_URL is used directly (same as before this change).
export const API_BASE_URL = import.meta.env.DEV ? DEV_API_BASE_URL : PROD_API_BASE_URL;

// WebSocket is unaffected: the browser lets WS connections cross origins
// (no CORS preflight for WS upgrades), so the direct backend URL is fine in
// both dev and prod.
export const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ||
  import.meta.env.REACT_WS_URL ||
  'ws://localhost:8000';

export const apiUrl = (path) => `${API_BASE_URL}${path}`;
export const wsUrl  = (path) => `${WS_BASE_URL}${path}`;
