import { createFileRoute } from '@tanstack/react-router';
import { ProductForm } from '@/components/admin/ProductForm';

export const Route = createFileRoute('/admin/products/new')({
  component: () => <ProductForm />,
});
