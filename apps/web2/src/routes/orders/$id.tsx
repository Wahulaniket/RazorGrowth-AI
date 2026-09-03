import { createFileRoute } from '@tanstack/react-router';
import { OrderDetailPage } from '@/components/orders/OrderDetailPage';

export const Route = createFileRoute('/orders/$id')({
  component: () => {
    const { id } = Route.useParams();
    return <OrderDetailPage id={id} />;
  },
});
