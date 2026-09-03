import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/growth')({
  component: () => <AdminGenericPage title='Growth' kicker='Experiments & insights' columns={['Name', 'Type', 'Status', 'Impact', 'Action']} rows={[]} />,
});
