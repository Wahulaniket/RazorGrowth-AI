import { createFileRoute } from '@tanstack/react-router';
import { ProductsPage } from '@/components/catalog/ProductsPage';

export const Route = createFileRoute('/products/')({
  component: ProductsPage,
});
