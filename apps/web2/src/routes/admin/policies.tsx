import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/policies')({
  component: () => <AdminGenericPage title='Policies' kicker='Commerce rules' columns={['Name', 'Type', 'Status', 'Action']} rows={[]} />,
});
