'use client';
import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient } from '../api/apiClient';
import { useAuth } from './AuthContext';
import { components } from '../api/schema';

export type CartResponse = components['schemas']['CartResponse'];

interface CartContextType {
  cart: CartResponse | null;
  loading: boolean;
  refreshCart: () => Promise<void>;
  addItem: (productId: string, quantity: number, variantId?: string) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType>({
  cart: null,
  loading: false,
  refreshCart: async () => {},
  addItem: async () => {},
  updateItem: async () => {},
  removeItem: async () => {},
  clearCart: async () => {},
});

export const CartProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      const { data } = await apiClient.GET('/api/v1/cart/');
      if (data) {
        setCart(data as CartResponse);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addItem = async (productId: string, quantity: number, variantId?: string) => {
    setLoading(true);
    try {
      await apiClient.POST('/api/v1/cart/items', {
        body: {
          product_id: productId,
          quantity: quantity,
          variant_id: variantId || null,
        }
      });
      await refreshCart();
    } finally {
      setLoading(false);
    }
  };

  const updateItem = async (itemId: string, quantity: number) => {
    setLoading(true);
    try {
      await apiClient.PUT('/api/v1/cart/items/{item_id}', {
        params: { path: { item_id: itemId } },
        body: { quantity }
      });
      await refreshCart();
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (itemId: string) => {
    setLoading(true);
    try {
      await apiClient.DELETE('/api/v1/cart/items/{item_id}', {
        params: { path: { item_id: itemId } }
      });
      await refreshCart();
    } finally {
      setLoading(false);
    }
  };
  
  const clearCart = async () => {
    setLoading(true);
    try {
      await apiClient.DELETE('/api/v1/cart/');
      await refreshCart();
    } finally {
      setLoading(false);
    }
  };

  return (
    <CartContext.Provider value={{ cart, loading, refreshCart, addItem, updateItem, removeItem, clearCart }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
