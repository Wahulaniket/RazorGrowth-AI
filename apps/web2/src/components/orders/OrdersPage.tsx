import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Status, money } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import { useQuery } from "@tanstack/react-query";

function OrderStatus({ status }: { status: string }) {
  return <Status tone={status === "PAID" || status === "DELIVERED" ? "success" : status === "CANCELLED" ? "error" : status === "PENDING" ? "warning" : "neutral"}>{status}</Status>;
}

export function OrdersPage() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      try {
        return await api.get("/api/v1/orders");
      } catch (error) {
        return [];
      }
    }
  });

  if (isLoading) return <CustomerShell><div className="py-20 text-center">Loading orders...</div></CustomerShell>;

  const orderList = Array.isArray(orders) ? orders : [];

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1280px] px-5 py-10 md:px-6">
        <p className="rg-kicker">Account / order history</p>
        <h1 className="mt-3 font-display text-5xl">Your orders.</h1>
        
        {orderList.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-rg-line bg-rg-panel p-10 text-center text-rg-cream-dim">
            You have no past orders.
          </div>
        ) : (
          <div className="mt-8 overflow-hidden rounded-2xl border border-rg-line bg-rg-panel">
            {orderList.map((order: any) => (
              <div key={order.id} className="grid gap-4 border-b border-rg-line p-5 last:border-0 md:grid-cols-[1.3fr_1fr_1fr_1fr_auto] md:items-center">
                <div>
                  <p className="text-xs text-rg-cream-dim">{new Date(order.created_at).toLocaleDateString()}</p>
                  <p className="mt-1 font-display text-2xl">#{order.id.slice(0, 8).toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-xs text-rg-cream-dim">Total</p>
                  <p className="mt-1">{money(order.total)}</p>
                </div>
                <div>
                  <p className="text-xs text-rg-cream-dim">Payment</p>
                  <div className="mt-1"><OrderStatus status={order.payment_status} /></div>
                </div>
                <div>
                  <p className="text-xs text-rg-cream-dim">Order status</p>
                  <div className="mt-1"><OrderStatus status={order.status} /></div>
                </div>
                <Button asChild variant="outline" className="rounded-full border-rg-line bg-transparent text-rg-cream hover:bg-rg-navy">
                  <Link to="/orders/$id" params={{ id: order.id }}>View order <ArrowRight /></Link>
                </Button>
              </div>
            ))}
          </div>
        )}
      </main>
    </CustomerShell>
  );
}
