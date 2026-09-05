import { useSyncExternalStore } from 'react';
import type { UserWithTenants } from '../types/api';

interface AuthState {
  token: string | null;
  tenantId: string | null;
  user: UserWithTenants | null;
}

const getInitialState = (): AuthState => {
  if (typeof window === 'undefined') {
    return { token: null, tenantId: null, user: null };
  }
  return {
    token: localStorage.getItem('rg_token'),
    tenantId: localStorage.getItem('rg_tenant_id'),
    user: null, // User is hydrated on demand or fetched on startup
  };
};

let state: AuthState = getInitialState();

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
  setAuth: (token: string, tenantId: string, user: UserWithTenants | null) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('rg_token', token);
      localStorage.setItem('rg_tenant_id', tenantId);
    }
    // Create a completely new state object to ensure React detects the change
    state = { token, tenantId, user };
    notify();
  },
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('rg_token');
      localStorage.removeItem('rg_tenant_id');
    }
    state = { token: null, tenantId: null, user: null };
    notify();
  },
  setUser: (user: UserWithTenants) => {
    state = { ...state, user };
    notify();
  }
};

// Safe for SSR
const getServerSnapshot = () => {
  return { token: null, tenantId: null, user: null };
};

export function useAuth() {
  return useSyncExternalStore(authStore.subscribe, authStore.getState, getServerSnapshot);
}
