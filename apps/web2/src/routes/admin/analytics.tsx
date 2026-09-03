import { createFileRoute } from '@tanstack/react-router';
import { AnalyticsPage } from '@/components/admin/AnalyticsPage';

export const Route = createFileRoute('/admin/analytics')({
  component: AnalyticsPage,
});
