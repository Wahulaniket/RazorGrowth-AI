import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Menu, ShoppingBag, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Brand() {
  return (
    <Link to="/" className="flex items-center gap-3 rg-focus">
      <span className="grid size-9 shrink-0 place-items-center rounded-full border border-rg-gold/60 font-display text-xl text-rg-gold">R</span>
      <span className="leading-none">
        <span className="block font-display text-xl text-rg-cream">RazorGrowth</span>
        <span className="mt-1 block text-[9px] uppercase tracking-[0.3em] text-rg-gold-soft">AI Commerce</span>
      </span>
    </Link>
  );
}

export function CustomerShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const count = 0; // TODO: get from cart store

  return (
    <div className="rg-page">
      <header className="border-b border-rg-line/70">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between gap-4 px-5 py-5 md:px-6">
          <Brand />
          <nav className="hidden items-center gap-8 text-sm text-rg-cream-dim md:flex">
            <Link to="/" activeProps={{ className: "text-rg-cream" }}>Home</Link>
            <Link to="/products" activeProps={{ className: "text-rg-cream" }}>Products</Link>
            <Link to="/ai" activeProps={{ className: "text-rg-cream" }}>AI Shopping</Link>
          </nav>
          <div className="flex items-center gap-2 sm:gap-5">
            <Link to="/orders" className="hidden text-sm text-rg-cream-dim sm:inline">Orders</Link>
            <Link to="/cart" className="relative rounded-full p-2 text-sm text-rg-cream-dim rg-focus">
              <ShoppingBag className="size-4" />
              <span className="absolute -right-1 -top-1 grid min-w-4 place-items-center rounded-full bg-rg-gold px-1 text-[10px] font-bold text-rg-ink">{count}</span>
            </Link>
            <Link to="/login" className="rounded-full bg-rg-gold px-4 py-2 text-sm font-medium text-rg-ink hover:bg-rg-gold-soft">Sign in</Link>
            <Button variant="ghost" size="icon" className="text-rg-cream-dim md:hidden" aria-label="Open navigation" onClick={() => setOpen(!open)}>
              {open ? <X /> : <Menu />}
            </Button>
          </div>
        </div>
        {open && (
          <nav className="border-t border-rg-line px-5 py-4 md:hidden">
            <div className="flex flex-col gap-4 text-sm text-rg-cream-dim">
              <Link to="/">Home</Link>
              <Link to="/products">Products</Link>
              <Link to="/ai">AI Shopping</Link>
              <Link to="/orders">Orders</Link>
            </div>
          </nav>
        )}
      </header>
      {children}
      <footer className="border-t border-rg-line/70">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-3 px-5 py-8 text-sm text-rg-cream-dim md:flex-row md:items-center md:justify-between md:px-6">
          <span className="font-display text-lg text-rg-cream">RazorGrowth AI</span>
          <span className="max-w-[42ch] text-xs">Every AI action is bounded, policy-checked, and auditable. Prices and payment are verified by the backend.</span>
          <span className="text-xs">© 2026 RazorGrowth</span>
        </div>
      </footer>
    </div>
  );
}
