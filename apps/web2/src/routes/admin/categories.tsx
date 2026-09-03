import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/categories')({
  component: () => <AdminGenericPage title='Categories' kicker='Catalog structure' columns={['Name', 'Products', 'Status', 'Action']} rows={[]} />,
});
