import { Outlet, createFileRoute, redirect, Link } from '@tanstack/react-router';
import { Package, Key, Home } from 'lucide-react';
import { authStore } from '@/lib/auth-store';

export const Route = createFileRoute('/admin')({
  beforeLoad: () => {
    const { token } = authStore.getState();
    if (!token) {
      throw redirect({ to: '/login' });
    }
  },
  component: AdminLayout,
});

function AdminLayout() {
  return (
    <div className="flex h-screen bg-rg-ink">
      <aside className="w-64 border-r border-rg-line bg-rg-panel flex flex-col">
        <div className="p-6 border-b border-rg-line">
          <Link to="/" className="flex items-center gap-2 text-rg-cream hover:text-rg-gold transition-colors">
            <span className="font-display text-xl tracking-wide uppercase">RazorGrowth AI</span>
          </Link>
          <span className="mt-2 block text-xs text-rg-cream-dim tracking-wider uppercase font-semibold">
            Merchant Center
          </span>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <Link
            to="/admin"
            className="flex items-center gap-3 px-3 py-2 text-sm text-rg-cream-dim rounded-lg hover:bg-rg-navy hover:text-rg-cream transition-colors [&.active]:bg-rg-gold/10 [&.active]:text-rg-gold"
          >
            <Home className="size-4" />
            Dashboard
          </Link>
          <Link
            to="/admin/products"
            className="flex items-center gap-3 px-3 py-2 text-sm text-rg-cream-dim rounded-lg hover:bg-rg-navy hover:text-rg-cream transition-colors [&.active]:bg-rg-gold/10 [&.active]:text-rg-gold"
          >
            <Package className="size-4" />
            Products
          </Link>
          <Link
            to="/admin/api-keys"
            className="flex items-center gap-3 px-3 py-2 text-sm text-rg-cream-dim rounded-lg hover:bg-rg-navy hover:text-rg-cream transition-colors [&.active]:bg-rg-gold/10 [&.active]:text-rg-gold"
          >
            <Key className="size-4" />
            API Keys
          </Link>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto bg-rg-ink text-rg-cream">
        <div className="p-8 max-w-5xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
