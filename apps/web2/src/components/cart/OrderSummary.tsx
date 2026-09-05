import { money } from "@/components/shared";

export function OrderSummary({ items = [] }: { items?: any[] }) {
  const subtotal = items.reduce((sum, item) => sum + (item.unit_price_snapshot || item.unit_price || 0) * item.quantity, 0);
  
  return (
    <div className="rounded-2xl border border-rg-line bg-rg-panel p-6">
      <p className="rg-kicker">Order summary</p>
      <div className="mt-5 space-y-3 text-sm">
        {items.map((item) => (
          <div key={item.id} className="flex justify-between gap-3 text-rg-cream-dim">
            <span>{item.product?.name || item.product_name || 'Product'} × {item.quantity}</span>
            <span className="shrink-0 text-rg-cream">{money((item.unit_price_snapshot || item.unit_price || 0) * item.quantity)}</span>
          </div>
        ))}
      </div>
      <div className="my-5 border-t border-rg-line" />
      <div className="flex justify-between text-sm text-rg-cream-dim">
        <span>Subtotal</span>
        <span>{money(subtotal)}</span>
      </div>
      <div className="mt-2 flex justify-between text-sm text-rg-cream-dim">
        <span>Tax</span>
        <span>Calculated by backend</span>
      </div>
      <div className="mt-4 flex justify-between font-display text-2xl text-rg-cream">
        <span>Total</span>
        <span>{money(subtotal)}</span>
      </div>
    </div>
  );
}
