import { AdminShell } from "@/components/layout/AdminShell";
import { money } from "@/components/shared";

export function AdminDashboardPage() {
  const metrics = [
    { label: "Total revenue", value: money(124000), trend: "+12%" },
    { label: "Orders", value: "482", trend: "+5%" },
    { label: "Active policies", value: "12", trend: "Stable" },
    { label: "AI conversion", value: "3.4%", trend: "+0.8%" },
  ];

  return (
    <AdminShell title="Dashboard">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-2xl border border-rg-line bg-rg-panel p-5">
            <p className="text-xs text-rg-cream-dim">{m.label}</p>
            <div className="mt-2 flex items-end justify-between gap-3">
              <span className="font-display text-3xl">{m.value}</span>
              <span className="text-xs text-rg-success">{m.trend}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-8 rounded-2xl border border-rg-line bg-rg-panel p-6">
        <p className="rg-kicker">Recent activity</p>
        <div className="mt-5 space-y-4">
          <p className="text-sm text-rg-cream-dim">No recent activity.</p>
        </div>
      </div>
    </AdminShell>
  );
}
