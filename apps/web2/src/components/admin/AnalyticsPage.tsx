import { AdminShell } from "@/components/layout/AdminShell";

export function AnalyticsPage() {
  return (
    <AdminShell title="Analytics">
      <p className="rg-kicker">Store performance</p>
      <div className="mt-6 rounded-2xl border border-rg-line bg-rg-panel p-6 text-center text-rg-cream-dim">
        <p>Analytics dashboard data will be populated from /api/v1/analytics.</p>
        <p className="mt-2 text-xs">For this demo, refer to the Growth tab for active experiments.</p>
      </div>
    </AdminShell>
  );
}
