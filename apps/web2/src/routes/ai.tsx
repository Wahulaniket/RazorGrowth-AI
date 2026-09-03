import { createFileRoute } from '@tanstack/react-router';
import { AIPage } from '@/components/agent/AIPage';

export const Route = createFileRoute('/ai')({
  component: AIPage
});
