import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/policies')({
  component: () => (
    <AdminGenericPage 
      title='Policies' 
      kicker='Commerce rules' 
      columns={['Name', 'Policy_Type', 'Status', 'Created_At']} 
      endpoint='/api/v1/policies' 
    />
  ),
});
