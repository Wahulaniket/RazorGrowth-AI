import { AdminShell } from "@/components/layout/AdminShell";

export function AdminGenericPage({ title, kicker, columns, rows }: { title: string; kicker: string; columns: string[]; rows: any[] }) {
  return (
    <AdminShell title={title}>
      <p className="rg-kicker">{kicker}</p>
      <div className="mt-6 overflow-hidden rounded-2xl border border-rg-line bg-rg-panel">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-rg-cream">
            <thead className="bg-rg-navy text-xs uppercase tracking-[0.15em] text-rg-cream-dim">
              <tr>
                {columns.map((col, i) => (
                  <th key={i} className="px-5 py-4 font-medium">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-rg-line">
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-5 py-10 text-center text-rg-cream-dim">No data available.</td>
                </tr>
              ) : (
                rows.map((row, i) => (
                  <tr key={i} className="hover:bg-rg-navy/50">
                    {columns.map((col, j) => (
                      <td key={j} className="px-5 py-4">{row[col.toLowerCase()] || "—"}</td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AdminShell>
  );
}
