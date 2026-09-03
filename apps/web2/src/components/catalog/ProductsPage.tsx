import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { CircleAlert, Search } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Status, money } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import heroImage from "@/assets/hero-headphones.jpg";

function ProductCard({ product, onAdd }: { product: any; onAdd?: (product: any) => void }) {
  return (
    <article className="rg-lift flex flex-col rounded-2xl border border-rg-line bg-rg-panel p-4">
      <Link to="/products/$id" params={{ id: product.id }} className="overflow-hidden rounded-xl rg-focus">
        <img src={heroImage} alt={product.name} width={800} height={600} loading="lazy" className="aspect-[4/3] w-full object-cover object-right transition duration-500 hover:scale-105" />
      </Link>
      <div className="mt-4 flex items-center justify-between">
        <span className="rg-kicker text-rg-gold/80">{product.category}</span>
        <span className="text-xs text-rg-warning">★ 4.8</span>
      </div>
      <Link to="/products/$id" params={{ id: product.id }} className="mt-1 font-display text-2xl leading-tight text-rg-cream rg-focus">
        {product.name}
      </Link>
      <p className="mt-2 text-xs leading-relaxed text-rg-cream-dim">{product.description}</p>
      <div className="mt-4 flex items-center justify-between gap-2">
        <span className="font-display text-xl text-rg-cream">{money(parseFloat(product.price))}</span>
        <Status tone="success">In stock</Status>
      </div>
      <div className="mt-4 flex gap-2">
        <Button onClick={() => onAdd?.(product)} className="flex-1 rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
          Add to cart
        </Button>
        <Button asChild variant="outline" className="rounded-full border-rg-line bg-transparent text-rg-cream hover:bg-rg-navy">
          <Link to="/products/$id" params={{ id: product.id }}>View</Link>
        </Button>
      </div>
    </article>
  );
}

export function ProductsPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");

  const { data, isLoading } = useQuery({
    queryKey: ['catalog', query, category],
    queryFn: async () => {
      return api.post("/api/v1/catalog/search", {
        query: query || null,
        category: category === "All" ? null : category,
        limit: 20
      });
    }
  });

  const addToCartMutation = useMutation({
    mutationFn: async (product: any) => {
      return api.post("/api/v1/cart/items", {
        product_id: product.id,
        quantity: 1,
      });
    },
    onSuccess: () => {
      toast.success("Added to cart");
    },
    onError: (error: any) => {
      if (error.status === 401) {
        toast.error("Please login to add to cart");
      } else {
        toast.error(error.data?.detail || "Failed to add to cart");
      }
    }
  });

  const categories = ["All", "Audio", "Computing", "Mobile", "Displays"];
  const list = data?.items || [];

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1280px] px-5 py-10 md:px-6">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="rg-kicker">Catalog / verified inventory</p>
            <h1 className="mt-3 font-display text-5xl text-rg-cream">Browse the collection.</h1>
          </div>
        </div>
        <div className="mt-8 grid gap-8 lg:grid-cols-[220px_1fr]">
          <aside className="rounded-2xl border border-rg-line bg-rg-panel p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-rg-cream-dim">Filters</p>
            <div className="mt-5 space-y-2">
              {categories.map((item) => (
                <Button key={item} variant="ghost" onClick={() => setCategory(item)} className={`w-full justify-start rounded-lg px-3 ${category === item ? "bg-rg-gold/15 text-rg-gold" : "text-rg-cream-dim"}`}>
                  {item}
                </Button>
              ))}
            </div>
            <div className="mt-8 border-t border-rg-line pt-5">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-rg-cream-dim">Availability</p>
              <label className="mt-4 flex items-center gap-2 text-sm text-rg-cream-dim">
                <input type="checkbox" defaultChecked className="accent-rg-gold" /> In stock
              </label>
            </div>
          </aside>
          <section>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 size-4 -translate-y-1/2 text-rg-cream-dim" />
                <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search products or categories" className="h-11 rounded-full border-rg-line bg-rg-panel pl-11 text-rg-cream placeholder:text-rg-cream-dim" aria-label="Search products" />
              </div>
            </div>
            {isLoading ? (
              <div className="mt-6 text-center text-rg-cream-dim">Loading products...</div>
            ) : (
              <>
                <div className="mt-6 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                  {list.map((product: any) => (
                    <ProductCard key={product.id} product={product} onAdd={(p) => addToCartMutation.mutate(p)} />
                  ))}
                </div>
                {list.length === 0 && (
                  <div className="mt-8 rounded-2xl border border-rg-line bg-rg-panel p-12 text-center">
                    <CircleAlert className="mx-auto size-7 text-rg-gold" />
                    <h2 className="mt-4 font-display text-3xl">No products found</h2>
                    <p className="mt-2 text-sm text-rg-cream-dim">Try another search or remove a filter.</p>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>
    </CustomerShell>
  );
}
