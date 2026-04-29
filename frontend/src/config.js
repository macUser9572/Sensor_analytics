export const API_BASE_URL = import.meta.env.REACT_API_BASE_URL;
export const WS_BASE_URL = import.meta.env.REACT_WS_URL;

if (!API_BASE_URL || !WS_BASE_URL) {
  throw new Error("REACT_API_BASE_URL and REACT_WS_URL must be set in .env");
}

export const apiUrl = (path) => `${API_BASE_URL}${path}`;
export const wsUrl = (path) => `${WS_BASE_URL}${path}`;
