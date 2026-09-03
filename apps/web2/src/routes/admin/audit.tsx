import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/audit')({
  component: () => <AdminGenericPage title='Audit logs' kicker='Compliance' columns={['Timestamp', 'Actor', 'Action', 'Resource', 'Result', 'Action']} rows={[]} />,
});
