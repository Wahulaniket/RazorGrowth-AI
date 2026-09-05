import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Minus, Plus, ShieldCheck, Package } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Status, money } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import heroImage from "@/assets/hero-headphones.jpg";

export function ProductDetailPage({ id }: { id: string }) {
  const [quantity, setQuantity] = useState(1);
  const [variant, setVariant] = useState<string | null>(null);

  const { data: product, isLoading } = useQuery({
    queryKey: ['product', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/catalog/products/${id}`);
      return res;
    }
  });

  const addToCartMutation = useMutation({
    mutationFn: async () => {
      const payload: any = {
        product_id: product.id,
        quantity,
      };
      if (variant) {
        payload.variant_id = variant;
      }
      return api.post("/api/v1/cart/items", payload);
    },
    onSuccess: () => {
      toast.success(`${product.name} added to cart`);
    },
    onError: (error: any) => {
      if (error.status === 401) {
        toast.error("Please login to add to cart");
      } else {
        toast.error(error.data?.detail || "Failed to add to cart");
      }
    }
  });

  if (isLoading) return <CustomerShell><div className="py-20 text-center">Loading...</div></CustomerShell>;
  if (!product) return <CustomerShell><div className="py-20 text-center">Product not found.</div></CustomerShell>;

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1280px] px-5 py-10 md:px-6">
        <div className="mb-8 text-xs text-rg-cream-dim">
          <Link to="/products" className="hover:text-rg-cream">Products</Link>
          <ChevronRight className="mx-2 inline size-3" />
          {product.category || "General"}
          <ChevronRight className="mx-2 inline size-3" />
          {product.name}
        </div>
        <div className="grid gap-10 lg:grid-cols-2">
          <div>
            <div className="overflow-hidden rounded-2xl border border-rg-line bg-rg-panel">
              <img src={heroImage} alt={product.name} width={1200} height={832} className="aspect-[4/3] w-full object-cover object-right" />
            </div>
          </div>
          <div>
            <p className="rg-kicker">{product.category} / Available</p>
            <h1 className="mt-3 font-display text-6xl leading-none text-rg-cream">{product.name}</h1>
            <p className="mt-6 text-base leading-relaxed text-rg-cream-dim">{product.description}</p>
            <div className="mt-8 flex items-baseline gap-3">
              <span className="font-display text-4xl text-rg-cream">{money(parseFloat(product.price))}</span>
              <Status tone="success">In stock</Status>
            </div>
            <div className="mt-8 grid gap-5 sm:grid-cols-2">
              <label className="text-sm text-rg-cream-dim">
                Variant
                <select value={variant || ""} onChange={(e) => setVariant(e.target.value)} className="mt-2 h-11 w-full rounded-lg border border-rg-line bg-rg-panel px-3 text-rg-cream">
                  {product.variants?.map((v: any) => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                  {(!product.variants || product.variants.length === 0) && <option>Default</option>}
                </select>
              </label>
              <div>
                <span className="text-sm text-rg-cream-dim">Quantity</span>
                <div className="mt-2 flex h-11 items-center justify-between rounded-lg border border-rg-line bg-rg-panel px-2">
                  <Button variant="ghost" size="icon" aria-label="Decrease quantity" onClick={() => setQuantity(Math.max(1, quantity - 1))}><Minus /></Button>
                  <span>{quantity}</span>
                  <Button variant="ghost" size="icon" aria-label="Increase quantity" onClick={() => setQuantity(quantity + 1)}><Plus /></Button>
                </div>
              </div>
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button onClick={() => addToCartMutation.mutate()} disabled={addToCartMutation.isPending} className="rounded-full bg-rg-gold px-7 text-rg-ink hover:bg-rg-gold-soft">
                {addToCartMutation.isPending ? "Adding..." : "Add to cart"}
              </Button>
            </div>
            <div className="mt-10 border-t border-rg-line pt-6">
              <p className="rg-kicker">Guarantees</p>
              <ul className="mt-4 space-y-3 text-sm text-rg-cream-dim">
                <li className="flex gap-3"><ShieldCheck className="size-4 shrink-0 text-rg-gold" /> Policy checked transactions</li>
                <li className="flex gap-3"><Package className="size-4 shrink-0 text-rg-gold" /> Inventory validated before cart and checkout.</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </CustomerShell>
  );
}
