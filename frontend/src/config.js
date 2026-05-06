export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.REACT_API_BASE_URL ||
  'http://localhost:8000';

export const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ||
  import.meta.env.REACT_WS_URL ||
  'ws://localhost:8000';

export const apiUrl = (path) => `${API_BASE_URL}${path}`;
export const wsUrl = (path) => `${WS_BASE_URL}${path}`;
