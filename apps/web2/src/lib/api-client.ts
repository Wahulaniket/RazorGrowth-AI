import { authStore } from './auth-store';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(public status: number, public data: any) {
    super(data?.detail || data?.error?.message || `API Error: ${status}`);
    this.name = 'APIError';
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const { token, tenantId } = authStore.getState();
  
  const headers = new Headers(options.headers);
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (tenantId && !headers.has('X-Tenant-ID')) {
    headers.set('X-Tenant-ID', tenantId);
  }
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
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
    
    // Only logout on 401 if it's not a login attempt
    if (response.status === 401 && !url.includes('/auth/login')) {
      authStore.logout();
      // Only redirect if we are in the browser
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    throw new APIError(response.status, errorData);
  }

  // Handle empty responses (like 204 No Content) gracefully
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  get: (url: string, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'GET' }),
  post: (url: string, body?: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: (url: string, body?: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: (url: string, body?: any, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: (url: string, options?: RequestInit) => fetchWithAuth(url, { ...options, method: 'DELETE' }),
};
