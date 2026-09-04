import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/growth')({
  component: () => (
    <AdminGenericPage 
      title='Growth & Recommendations' 
      kicker='AI Recommendation Rules' 
      columns={['ID', 'Product_ID', 'Score', 'Created_At']} 
      endpoint='/api/v1/recommendations' 
    />
  ),
});
