import { authStore } from './auth-store';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, public data: any) {
    super(`API Error: ${status}`);
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const { token, tenantId } = authStore.getState();
  
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (tenantId) {
    headers.set('X-Tenant-ID', tenantId);
  }
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    if (response.status === 401) {
      authStore.logout();
    }
    throw new APIError(response.status, errorData);
  }

  return response.json();
}

export const api = {
  get: (url: string, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'GET' }),
  post: (url: string, body: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: (url: string, body: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  patch: (url: string, body: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'PATCH', body: JSON.stringify(body) }),
  delete: (url: string, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'DELETE' }),
};
