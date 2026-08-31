'use client';

import { useCart } from '@/lib/contexts/CartContext';
import { Navbar } from '@/components/navbar';
import { Button } from '@/components/ui/button';
import { Trash2, Plus, Minus, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function CartPage() {
  const { cart, loading, updateItem, removeItem, clearCart } = useCart();

  if (loading && !cart) {
    return (
      <div className="flex flex-col h-full min-h-screen bg-gray-50">
        <Navbar />
        <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">
          <p>Loading cart...</p>
        </main>
      </div>
    );
  }

  const items = cart?.items || [];
  const totalItems = items.reduce((acc: number, item: any) => acc + item.quantity, 0);

  return (
    <div className="flex flex-col h-full min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 h-full">
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Your Shopping Cart</h1>
        
        {items.length === 0 ? (
          <div className="text-center py-16 bg-white border rounded-xl shadow-sm">
            <h2 className="text-2xl font-semibold text-gray-700">Your cart is empty</h2>
            <p className="mt-2 text-gray-500">Looks like you haven't added anything yet.</p>
            <Link href="/">
              <Button className="mt-6 px-8 rounded-full">Continue Shopping</Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8 space-y-4">
              {items.map((item: any) => (
                <div key={item.id} className="flex items-center p-4 bg-white border rounded-xl shadow-sm">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900">{item.product?.name || 'Unknown Product'}</h3>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-1">{item.product?.description}</p>
                    <div className="mt-4 flex items-center gap-4">
                      <div className="flex items-center border rounded-full overflow-hidden">
                        <button 
                          onClick={() => updateItem(item.id, Math.max(1, item.quantity - 1))}
                          className="px-3 py-1 hover:bg-gray-100 transition-colors text-gray-600"
                          disabled={loading}
                        >
                          <Minus size={14} />
                        </button>
                        <span className="px-3 py-1 text-sm font-medium w-8 text-center">{item.quantity}</span>
                        <button 
                          onClick={() => updateItem(item.id, item.quantity + 1)}
                          className="px-3 py-1 hover:bg-gray-100 transition-colors text-gray-600"
                          disabled={loading}
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                      <button 
                        onClick={() => removeItem(item.id)}
                        className="text-red-500 hover:text-red-600 p-2 rounded-full hover:bg-red-50 transition-colors"
                        title="Remove item"
                        disabled={loading}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                  <div className="ml-4 flex flex-col items-end">
                    <span className="font-bold text-xl">
                      {item.product?.currency === 'INR' ? '₹' : item.product?.currency} {item.unit_price}
                    </span>
                    <span className="text-sm text-gray-500 mt-1">Total: ₹{item.line_total}</span>
                  </div>
                </div>
              ))}
              <div className="flex justify-end pt-4">
                <Button variant="outline" onClick={clearCart} disabled={loading} className="text-red-600 border-red-200 hover:bg-red-50">
                  Clear Cart
                </Button>
              </div>
            </div>
            
            <div className="lg:col-span-4">
              <div className="bg-white border rounded-xl p-6 shadow-sm sticky top-8">
                <h3 className="text-xl font-semibold mb-4">Order Summary</h3>
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal ({totalItems} items)</span>
                    <span>₹{cart.subtotal_amount}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Tax</span>
                    <span>₹{cart.tax_amount}</span>
                  </div>
                  <div className="border-t pt-3 flex justify-between font-bold text-xl text-gray-900">
                    <span>Total</span>
                    <span>₹{cart.total_amount}</span>
                  </div>
                </div>
                <Link href="/checkout">
                  <Button className="w-full h-12 rounded-full text-lg" disabled={loading}>
                    Proceed to Checkout
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
