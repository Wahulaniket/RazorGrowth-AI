import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/orders')({
  component: () => (
    <AdminGenericPage 
      title='Orders' 
      kicker='Fulfillment' 
      columns={['ID', 'Total', 'Currency', 'Status', 'Payment_Status', 'Created_At']} 
      endpoint='/api/v1/orders/' 
    />
  ),
});
