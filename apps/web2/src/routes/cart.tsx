import { createFileRoute, redirect } from '@tanstack/react-router';
import { CartPage } from '@/components/cart/CartPage';
import { authStore } from '@/lib/auth-store';

export const Route = createFileRoute('/cart')({
  beforeLoad: () => {
    const { token } = authStore.getState();
    if (!token) {
      throw redirect({ to: '/login' });
    }
  },
  component: CartPage,
});
