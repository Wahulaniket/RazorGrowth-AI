import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowRight, Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { money } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { OrderSummary } from "./OrderSummary";
import { api } from "@/lib/api-client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import heroImage from "@/assets/hero-headphones.jpg";

export function CartPage() {
  const queryClient = useQueryClient();

  const { data: cart, isLoading } = useQuery({
    queryKey: ['cart'],
    queryFn: async () => {
      try {
        return await api.get("/api/v1/cart/");
      } catch (error: any) {
        if (error.status === 404) return { items: [] };
        throw error;
      }
    },
    retry: false
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, quantity }: { id: string; quantity: number }) => {
      if (quantity === 0) {
        return api.delete(`/api/v1/cart/items/${id}`);
      }
      return api.put(`/api/v1/cart/items/${id}`, { quantity });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
    onError: (error: any) => {
      toast.error(error.data?.detail || "Failed to update cart");
    }
  });

  const items = cart?.items || [];

  if (isLoading) return <CustomerShell><div className="py-20 text-center">Loading...</div></CustomerShell>;

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1280px] px-5 py-10 md:px-6">
        <p className="rg-kicker">Cart / inventory-aware</p>
        <h1 className="mt-3 font-display text-5xl text-rg-cream">Your cart.</h1>
        {items.length === 0 ? (
          <div className="mt-10 rounded-2xl border border-rg-line bg-rg-panel p-14 text-center">
            <ShoppingBag className="mx-auto size-8 text-rg-gold" />
            <h2 className="mt-5 font-display text-4xl">Your cart is empty</h2>
            <p className="mt-2 text-sm text-rg-cream-dim">Discover something you'll love.</p>
            <Button asChild className="mt-7 rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
              <Link to="/products">Start shopping</Link>
            </Button>
          </div>
        ) : (
          <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_360px]">
            <section className="space-y-4">
              {items.map((item: any) => (
                <div key={item.id} className="flex gap-4 rounded-2xl border border-rg-line bg-rg-panel p-4">
                  <img src={heroImage} alt={item.product?.name || "Product"} width={160} height={120} className="size-24 rounded-xl object-cover object-right sm:size-32" />
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between gap-3">
                      <div>
                        <p className="text-xs text-rg-cream-dim">{item.product?.category || 'Category'} · Default</p>
                        <h2 className="mt-1 font-display text-2xl text-rg-cream">{item.product?.name || 'Product'}</h2>
                      </div>
                      <Button variant="ghost" size="icon" aria-label={`Remove`} className="text-rg-cream-dim hover:text-rg-error" onClick={() => updateMutation.mutate({ id: item.id, quantity: 0 })}>
                        <Trash2 />
                      </Button>
                    </div>
                    <div className="mt-5 flex items-center justify-between">
                      <span className="font-display text-xl">{money(item.unit_price)}</span>
                      <div className="flex items-center rounded-lg border border-rg-line">
                        <Button variant="ghost" size="icon" aria-label="Decrease quantity" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate({ id: item.id, quantity: item.quantity - 1 })}>
                          <Minus />
                        </Button>
                        <span className="w-8 text-center text-sm">{item.quantity}</span>
                        <Button variant="ghost" size="icon" aria-label="Increase quantity" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate({ id: item.id, quantity: item.quantity + 1 })}>
                          <Plus />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </section>
            <aside>
              <OrderSummary items={items} />
              <Button asChild className="mt-4 w-full rounded-full bg-rg-gold py-3 text-rg-ink hover:bg-rg-gold-soft">
                <Link to="/checkout">Proceed to checkout <ArrowRight /></Link>
              </Button>
              <Button asChild variant="ghost" className="mt-2 w-full text-rg-cream-dim">
                <Link to="/products">Continue shopping</Link>
              </Button>
            </aside>
          </div>
        )}
      </main>
    </CustomerShell>
  );
}
