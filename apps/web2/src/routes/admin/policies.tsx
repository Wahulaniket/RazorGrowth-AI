import { createFileRoute } from '@tanstack/react-router';
import { PoliciesPage } from '@/components/admin/PoliciesPage';

export const Route = createFileRoute('/admin/policies')({
  component: () => <PoliciesPage />,
});
