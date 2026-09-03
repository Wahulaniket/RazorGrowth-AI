import { Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { AdminShell } from "@/components/layout/AdminShell";
import { Status, money } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import { useQuery } from "@tanstack/react-query";

export function AdminProductsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-products'],
    queryFn: () => api.post("/api/v1/catalog/search", { limit: 50 })
  });
  
  const products = data?.items || [];

  return (
    <AdminShell title="Products">
      <div className="flex items-center justify-between">
        <p className="rg-kicker">Catalog management</p>
        <Button className="rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft"><Plus className="mr-2 size-4" /> Add product</Button>
      </div>
      <div className="mt-6 overflow-hidden rounded-2xl border border-rg-line bg-rg-panel">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-rg-cream">
            <thead className="bg-rg-navy text-xs uppercase tracking-[0.15em] text-rg-cream-dim">
              <tr>
                <th className="px-5 py-4 font-medium">Product</th>
                <th className="px-5 py-4 font-medium">Category</th>
                <th className="px-5 py-4 font-medium">Price</th>
                <th className="px-5 py-4 font-medium">Inventory</th>
                <th className="px-5 py-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rg-line">
              {isLoading ? (
                <tr><td colSpan={5} className="px-5 py-10 text-center text-rg-cream-dim">Loading...</td></tr>
              ) : products.length === 0 ? (
                <tr><td colSpan={5} className="px-5 py-10 text-center text-rg-cream-dim">No products found.</td></tr>
              ) : (
                products.map((p: any) => (
                  <tr key={p.id} className="hover:bg-rg-navy/50">
                    <td className="px-5 py-4">
                      <p className="font-semibold">{p.name}</p>
                      <p className="text-xs text-rg-cream-dim">{p.id.slice(0, 8)}</p>
                    </td>
                    <td className="px-5 py-4">{p.category}</td>
                    <td className="px-5 py-4">{money(parseFloat(p.price))}</td>
                    <td className="px-5 py-4"><Status tone="success">In stock</Status></td>
                    <td className="px-5 py-4"><Button variant="ghost" className="text-xs text-rg-gold hover:text-rg-gold-soft">Edit</Button></td>
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
