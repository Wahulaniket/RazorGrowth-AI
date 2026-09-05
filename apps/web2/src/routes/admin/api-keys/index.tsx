import { createFileRoute } from '@tanstack/react-router';
import { ApiKeysPage } from '@/components/admin/ApiKeysPage';

export const Route = createFileRoute('/admin/api-keys/')({
  component: () => <ApiKeysPage />,
});
