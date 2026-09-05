import { createFileRoute, redirect } from '@tanstack/react-router';
import { AuthPage } from '@/components/auth/AuthPage';
import { authStore } from '@/lib/auth-store';

export const Route = createFileRoute('/register')({
  beforeLoad: () => {
    const { token } = authStore.getState();
    if (token) {
      throw redirect({ to: '/' });
    }
  },
  component: () => <AuthPage register={true} />
});
