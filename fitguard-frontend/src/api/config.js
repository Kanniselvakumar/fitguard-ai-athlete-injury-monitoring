const defaultApiBaseUrl = 'http://localhost:5000/api';

const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl).replace(/\/+$/, '');

export const API_BASE_URL = configuredApiBaseUrl;
export const API_ORIGIN = new URL(configuredApiBaseUrl).origin;

export function resolveApiUrl(path) {
  if (!path) {
    return '';
  }

  try {
    return new URL(path).toString();
  } catch {
    return new URL(path, `${API_ORIGIN}/`).toString();
  }
}
