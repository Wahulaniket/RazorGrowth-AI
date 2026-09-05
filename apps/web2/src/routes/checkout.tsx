import { createFileRoute, redirect } from '@tanstack/react-router';
import { CheckoutPage } from '@/components/checkout/CheckoutPage';
import { authStore } from '@/lib/auth-store';

export const Route = createFileRoute('/checkout')({
  beforeLoad: () => {
    const { token } = authStore.getState();
    if (!token) {
      throw redirect({ to: '/login' });
    }
  },
  component: CheckoutPage,
});
