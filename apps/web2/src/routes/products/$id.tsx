import { createFileRoute } from '@tanstack/react-router';
import { ProductDetailPage } from '@/components/catalog/ProductDetailPage';

export const Route = createFileRoute('/products/$id')({
  component: () => {
    const { id } = Route.useParams();
    return <ProductDetailPage id={id} />;
  },
});
