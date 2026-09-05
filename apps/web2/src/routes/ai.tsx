import { createFileRoute, redirect } from '@tanstack/react-router';
import { AIPage } from '@/components/agent/AIPage';
import { authStore } from '@/lib/auth-store';

export const Route = createFileRoute('/ai')({
  beforeLoad: () => {
    const { token } = authStore.getState();
    if (!token) {
      throw redirect({ to: '/login' });
    }
  },
  component: AIPage
});
