import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/customers')({
  component: () => (
    <AdminGenericPage 
      title='Customers' 
      kicker='User base' 
      columns={['Name', 'Email', 'Status', 'Created_At']} 
      missingMessage="GET /api/v1/customers (or /api/v1/users) list endpoint is missing on backend for tenant admins."
    />
  ),
});
