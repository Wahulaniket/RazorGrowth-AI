import { useSyncExternalStore } from 'react';

interface AuthState {
  token: string | null;
  tenantId: string | null;
  user: any | null;
}

let state: AuthState = {
  token: typeof window !== 'undefined' ? localStorage.getItem('rg_token') : null,
  tenantId: typeof window !== 'undefined' ? localStorage.getItem('rg_tenant_id') : null,
  user: null,
};

const listeners = new Set<() => void>();

function notify() {
  for (const listener of listeners) {
    listener();
  }
}

export const authStore = {
  getState: () => state,
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setAuth: (token: string, tenantId: string, user: any) => {
    localStorage.setItem('rg_token', token);
    localStorage.setItem('rg_tenant_id', tenantId);
    state = { token, tenantId, user };
    notify();
  },
  logout: () => {
    localStorage.removeItem('rg_token');
    localStorage.removeItem('rg_tenant_id');
    state = { token: null, tenantId: null, user: null };
    notify();
  },
  setUser: (user: any) => {
    state = { ...state, user };
    notify();
  }
};

export function useAuth() {
  return useSyncExternalStore(authStore.subscribe, authStore.getState, authStore.getState);
}
