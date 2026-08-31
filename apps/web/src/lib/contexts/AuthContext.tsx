'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../api/apiClient';
import { components } from '../api/schema';

export type User = components['schemas']['UserResponse'];

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string, tenantSlug: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = async () => {
    try {
      const { data, error } = await apiClient.GET('/api/v1/auth/me');
      if (data) {
        setUser(data as User);
      } else {
        setUser(null);
      }
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const login = async (token: string, tenantSlug: string) => {
    localStorage.setItem('token', token);
    localStorage.setItem('tenantSlug', tenantSlug);
    await loadUser();
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('tenantSlug');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
