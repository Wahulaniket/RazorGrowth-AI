import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { BarChart3, ClipboardList, Grid2X2, LayoutDashboard, Menu, Package, ShieldCheck, ShoppingBag, Store, TrendingUp, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Brand } from "./CustomerShell";

const adminNav = [
  { label: "Dashboard", to: "/admin", icon: LayoutDashboard },
  { label: "Products", to: "/admin/products", icon: Package },
  { label: "Categories", to: "/admin/categories", icon: Grid2X2 },
  { label: "Orders", to: "/admin/orders", icon: ClipboardList },
  { label: "Customers", to: "/admin/customers", icon: Users },
  { label: "Analytics", to: "/admin/analytics", icon: BarChart3 },
  { label: "Growth", to: "/admin/growth", icon: TrendingUp },
  { label: "Policies", to: "/admin/policies", icon: ShieldCheck },
  { label: "Audit logs", to: "/admin/audit", icon: Store }
];

export function AdminShell({ children, title }: { children: React.ReactNode; title: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-rg-ink text-rg-cream">
      <aside className={`fixed inset-y-0 left-0 z-30 w-64 border-r border-rg-line bg-rg-navy p-5 transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <Brand />
        <div className="mt-10 space-y-1">
          {adminNav.map(({ label, to, icon: Icon }) => (
            <Link key={to} to={to} activeProps={{ className: "bg-rg-gold/15 text-rg-gold" }} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-rg-cream-dim hover:bg-rg-panel hover:text-rg-cream">
              <Icon className="size-4" />{label}
            </Link>
          ))}
        </div>
        <div className="absolute bottom-5 left-5 right-5 border-t border-rg-line pt-5">
          <Link to="/" className="flex items-center gap-3 px-3 text-sm text-rg-cream-dim">
            <ShoppingBag className="size-4" />View storefront
          </Link>
        </div>
      </aside>
      {open && <button className="fixed inset-0 z-20 bg-rg-ink/70 lg:hidden" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-rg-line/70 bg-rg-ink/90 backdrop-blur">
          <div className="flex items-center justify-between px-5 py-4 md:px-8">
            <Button variant="ghost" size="icon" className="text-rg-cream-dim lg:hidden" aria-label="Open admin navigation" onClick={() => setOpen(true)}>
              <Menu />
            </Button>
            <div className="min-w-0">
              <p className="rg-kicker">RazorGrowth Store / merchant</p>
              <h1 className="mt-1 truncate font-display text-3xl">{title}</h1>
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden text-xs text-rg-cream-dim sm:inline">RazorGrowth Store</span>
              <span className="grid size-9 place-items-center rounded-full bg-rg-gold text-sm font-semibold text-rg-ink">AR</span>
            </div>
          </div>
        </header>
        <main className="px-5 py-8 md:px-8">{children}</main>
      </div>
    </div>
  );
}
