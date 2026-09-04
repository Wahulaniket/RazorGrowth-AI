import { createFileRoute } from '@tanstack/react-router';
import { AdminGenericPage } from '@/components/admin/AdminGenericPage';

export const Route = createFileRoute('/admin/audit')({
  component: () => (
    <AdminGenericPage 
      title='Audit logs' 
      kicker='Compliance' 
      columns={['Timestamp', 'Actor', 'Action', 'Resource', 'Result']} 
      missingMessage="GET /api/v1/audit endpoint is missing on backend. (Audit logs are written to PostgreSQL audit_logs table via AuditService.log_event)"
    />
  ),
});
