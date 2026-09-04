import { AdminShell } from "@/components/layout/AdminShell";

export function AnalyticsPage() {
  return (
    <AdminShell title="Analytics">
      <p className="rg-kicker">Store performance</p>
      <div className="mt-6 rounded-2xl border border-rg-warning/30 bg-rg-warning/10 p-6 text-center text-rg-warning font-semibold">
        <p>[BACKEND ENDPOINT MISSING]: GET /api/v1/analytics dashboard summary endpoint is not implemented on the backend.</p>
        <p className="mt-2 text-xs font-normal text-rg-cream-dim">Analytics events are tracked via POST /api/v1/analytics/events to the PostgreSQL analytics_events table.</p>
      </div>
    </AdminShell>
  );
}
