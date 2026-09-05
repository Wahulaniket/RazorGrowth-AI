import { Link } from "@tanstack/react-router";
import { Check } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Status, money } from "@/components/shared";
import { OrderSummary } from "@/components/cart/OrderSummary";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import { useQuery } from "@tanstack/react-query";
import heroImage from "@/assets/hero-headphones.jpg";

function OrderStatus({ status }: { status: string }) {
  return <Status tone={status === "PAID" || status === "DELIVERED" ? "success" : status === "CANCELLED" ? "error" : status === "PENDING" ? "warning" : "neutral"}>{status}</Status>;
}

export function OrderDetailPage({ id }: { id: string }) {
  const { data: order, isLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: async () => {
      try {
        return await api.get(`/api/v1/orders/${id}`);
      } catch (error) {
        return null;
      }
    }
  });

  if (isLoading) return <CustomerShell><div className="py-20 text-center">Loading...</div></CustomerShell>;
  if (!order) return <CustomerShell><div className="py-20 text-center">Order not found.</div></CustomerShell>;

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1100px] px-5 py-10 md:px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="rg-kicker">Order confirmation</p>
            <h1 className="mt-3 font-display text-5xl">Order placed successfully.</h1>
            <p className="mt-2 text-sm text-rg-cream-dim">Order #{order.id.slice(0, 8).toUpperCase()} · {new Date(order.created_at).toLocaleDateString()}</p>
          </div>
          <OrderStatus status={order.status} />
        </div>
        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_340px]">
          <section className="space-y-5">
            <div className="rounded-2xl border border-rg-success/30 bg-rg-success/10 p-5">
              <div className="flex items-center gap-2 font-semibold text-rg-success">
                <Check className="size-4" /> Payment status: {order.payment_status}
              </div>
              <p className="mt-2 text-sm text-rg-cream-dim">Payment status is confirmed by the backend payment provider.</p>
            </div>
            
            <div className="rounded-2xl border border-rg-line bg-rg-panel p-6">
              <p className="rg-kicker">Items</p>
              <div className="mt-5 space-y-4">
                {order.items?.map((item: any) => (
                  <div key={item.id} className="flex items-center gap-4">
                    <img src={heroImage} alt={item.product_name || "Product"} width={80} height={60} className="size-16 rounded-lg object-cover object-right" />
                    <div className="flex-1">
                      <p className="font-display text-xl">{item.product_name || "Product"}</p>
                      <p className="text-xs text-rg-cream-dim">Default · Qty {item.quantity}</p>
                    </div>
                    <span>{money(item.unit_price * item.quantity)}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="rounded-2xl border border-rg-line bg-rg-panel p-6">
              <p className="rg-kicker">Order timeline</p>
              <div className="mt-6 flex items-start gap-3">
                <span className="mt-1 size-2 rounded-full bg-rg-gold" />
                <div>
                  <p className="text-sm text-rg-cream">Order created</p>
                  <p className="text-xs text-rg-cream-dim">Backend confirmed inventory, policy, and payment.</p>
                </div>
              </div>
              <div className="ml-1 mt-1 h-8 border-l border-dashed border-rg-line" />
              <div className="flex items-start gap-3">
                <span className="mt-1 size-2 rounded-full bg-rg-success" />
                <div>
                  <p className="text-sm text-rg-cream">{order.status}</p>
                  <p className="text-xs text-rg-cream-dim">Tracking updates will appear here.</p>
                </div>
              </div>
            </div>
          </section>
          <aside>
            <OrderSummary items={order.items || []} />
            <div className="mt-4 flex flex-col gap-2">
              <Button asChild className="rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
                <Link to="/products">Continue shopping</Link>
              </Button>
              <Button asChild variant="ghost" className="rounded-full text-rg-cream-dim">
                <Link to="/orders">View all orders</Link>
              </Button>
            </div>
          </aside>
        </div>
      </main>
    </CustomerShell>
  );
}
