import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Status } from "@/components/shared";
import { api } from "@/lib/api-client";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";

import heroImage from "@/assets/hero-headphones.jpg";

function ProductCard({ product, onAdd }: { product: any; onAdd?: (product: any) => void }) {
  return (
    <article className="rg-lift flex flex-col rounded-2xl border border-rg-line bg-rg-panel p-4">
      <Link to="/products/$id" params={{ id: product.product_id }} className="overflow-hidden rounded-xl rg-focus">
        <img src={heroImage} alt={product.name} width={800} height={600} loading="lazy" className="aspect-[4/3] w-full object-cover object-right transition duration-500 hover:scale-105" />
      </Link>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-rg-warning">★ 4.8</span>
      </div>
      <Link to="/products/$id" params={{ id: product.product_id }} className="mt-1 font-display text-2xl leading-tight text-rg-cream rg-focus">
        {product.name}
      </Link>
      <div className="mt-2 space-y-1">
        {product.reasons?.map((r: string, i: number) => (
          <p key={i} className="text-xs leading-relaxed text-rg-cream-dim">• {r}</p>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between gap-2">
        <span className="font-display text-xl text-rg-cream">{product.currency} {product.price}</span>
        <Status tone="success">In Stock</Status>
      </div>
      <div className="mt-4 flex gap-2">
        <Button onClick={() => onAdd?.(product)} className="flex-1 rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
          Add to cart
        </Button>
        <Button asChild variant="outline" className="rounded-full border-rg-line bg-transparent text-rg-cream hover:bg-rg-navy">
          <Link to="/products/$id" params={{ id: product.product_id }}>View</Link>
        </Button>
      </div>
    </article>
  );
}

function ActionCard({ item, onConfirm }: { item: any; onConfirm: () => void }) {
  const [state, setState] = useState<"pending" | "done" | "cancelled">("pending");

  if (state === "done") {
    return (
      <div className="rounded-2xl border border-rg-success/30 bg-rg-success/10 p-5">
        <div className="flex items-center gap-2 text-sm font-semibold text-rg-success"><Check className="size-4" /> Action completed</div>
        <p className="mt-2 text-sm text-rg-cream-dim">The product was added after availability and policy checks.</p>
      </div>
    );
  }
  
  if (state === "cancelled") {
    return (
      <div className="rounded-2xl border border-rg-line bg-rg-navy p-5">
        <p className="text-sm text-rg-cream-dim">Action cancelled. Nothing was added to your cart.</p>
        <Button variant="ghost" className="mt-2 px-0 text-rg-gold" onClick={() => setState("pending")}>Review again</Button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-rg-gold/40 bg-rg-navy p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="rg-kicker text-rg-gold">AI action</p>
        <Status tone="warning">Confirmation required</Status>
      </div>
      <p className="mt-3 text-sm text-rg-cream">Add 1 × {item.name} to your cart.</p>
      <ul className="mt-4 space-y-2 text-xs text-rg-cream-dim">
        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-rg-success" /> Product available</li>
        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-rg-success" /> Policy approved</li>
        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-rg-gold" /> Your confirmation needed</li>
      </ul>
      <div className="mt-5 flex gap-3">
        <Button variant="outline" className="flex-1 rounded-full border-rg-line bg-transparent text-rg-cream hover:bg-rg-panel" onClick={() => setState("cancelled")}>Cancel</Button>
        <Button className="flex-1 rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft" onClick={() => { onConfirm(); setState("done"); }}>Confirm</Button>
      </div>
    </div>
  );
}

export function AIPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string; data?: any }[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      return api.post("/api/v1/agent/chat", {
        message,
        session_id: sessionId
      });
    },
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.message, data: data }
      ]);
    },
    onError: (error: any) => {
      toast.error(error.data?.detail || "Agent chat failed");
    }
  });

  const addToCartMutation = useMutation({
    mutationFn: async (product: any) => {
      return api.post("/api/v1/cart/items", {
        product_id: product.product_id,
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

  const send = (value: string) => {
    if (!value.trim()) return;
    setMessages((prev) => [...prev, { role: "user", text: value.trim() }]);
    setInput("");
    chatMutation.mutate(value.trim());
  };

  const latestData = messages.findLast(m => m.role === "ai")?.data;
  const recommendations = latestData?.recommendations || [];

  return (
    <CustomerShell>
      <main className="mx-auto grid max-w-[1280px] gap-10 px-5 py-10 md:px-6 lg:grid-cols-[0.85fr_1.15fr]">
        <section>
          <p className="rg-kicker">Conversational commerce / live session</p>
          <h1 className="mt-3 font-display text-5xl text-rg-cream">Tell us what you need.</h1>
          <p className="mt-3 max-w-[38ch] text-sm leading-relaxed text-rg-cream-dim">
            The agent understands intent, verifies the catalog, and asks before taking a bounded action.
          </p>
          
          <div className="mt-8 space-y-4 max-h-[50vh] overflow-y-auto pr-2">
            {messages.map((m, i) => (
              <div key={i}>
                {m.role === "user" ? (
                  <div className="ml-auto max-w-[88%] rounded-2xl rounded-tr-sm border border-rg-gold/30 bg-rg-gold/15 px-4 py-3 text-sm">
                    {m.text}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="rounded-2xl rounded-tl-sm border border-rg-line bg-rg-panel px-4 py-4 text-sm leading-relaxed text-rg-cream">
                      {m.text}
                    </div>
                    {m.data?.recommendations?.length > 0 && (
                      <ActionCard 
                        item={m.data.recommendations[0]} 
                        onConfirm={() => addToCartMutation.mutate(m.data.recommendations[0])} 
                      />
                    )}
                  </div>
                )}
              </div>
            ))}
            
            {chatMutation.isPending && (
              <div className="flex items-center gap-2 rounded-2xl border border-rg-line bg-rg-panel px-4 py-4 text-sm text-rg-cream-dim">
                <span className="size-2 animate-pulse rounded-full bg-rg-gold" /> Thinking through catalog and policy checks…
              </div>
            )}
          </div>
          
          <div className="mt-8">
            <p className="text-xs text-rg-cream-dim">Suggested prompts</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {["Find me a laptop for programming", "Best headphones under ₹10,000", "Show me gaming monitors"].map((prompt) => (
                <Button key={prompt} variant="outline" className="rounded-full border-rg-line bg-transparent text-xs text-rg-cream-dim hover:bg-rg-panel" onClick={() => send(prompt)}>
                  {prompt}
                </Button>
              ))}
            </div>
          </div>
          <div className="mt-8 flex gap-2">
            <Input 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              onKeyDown={(e) => e.key === "Enter" && send(input)} 
              placeholder="Describe what you're shopping for…" 
              className="h-12 rounded-full border-rg-line bg-rg-panel px-5 text-rg-cream placeholder:text-rg-cream-dim" 
              disabled={chatMutation.isPending}
            />
            <Button onClick={() => send(input)} disabled={chatMutation.isPending} className="size-12 shrink-0 rounded-full bg-rg-gold p-0 text-rg-ink hover:bg-rg-gold-soft">
              <ArrowRight />
            </Button>
          </div>
        </section>
        
        <section>
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="rg-kicker">Verified picks</p>
              <h2 className="mt-2 font-display text-4xl text-rg-cream">Recommended for you</h2>
            </div>
            <span className="text-xs text-rg-cream-dim">{recommendations.length} matches</span>
          </div>
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            {recommendations.map((product: any) => (
              <ProductCard key={product.product_id} product={product} onAdd={(item) => addToCartMutation.mutate(item)} />
            ))}
          </div>
        </section>
      </main>
    </CustomerShell>
  );
}
