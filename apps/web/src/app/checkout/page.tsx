'use client';

import { useCart } from '@/lib/contexts/CartContext';
import { Navbar } from '@/components/navbar';
import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/apiClient';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function CheckoutPage() {
  const { cart, loading: cartLoading } = useCart();
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
    
    if (cart && cart.items.length > 0 && !quote && !loading) {
      createQuote();
    }
  }, [cart]);

  const createQuote = async () => {
    setLoading(true);
    try {
      const { data, error } = await apiClient.POST('/api/v1/checkout/quote');
      if (error) throw new Error((error as any).detail || 'Failed to create quote');
      setQuote(data);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  const confirmAndPay = async () => {
    setLoading(true);
    try {
      // 1. Confirm quote
      const { data: orderData, error: orderError } = await apiClient.POST('/api/v1/checkout/{quote_id}/confirm', {
        params: { path: { quote_id: quote.id } }
      });
      if (orderError) throw new Error((orderError as any).detail || 'Failed to confirm quote');

      // 2. Create Payment
      const { data: paymentData, error: paymentError } = await apiClient.POST('/api/v1/payments', {
        body: { order_id: orderData.id } as any // typing workaround
      });
      if (paymentError) throw new Error((paymentError as any).detail || 'Failed to initialize payment');

      // 3. Open Razorpay
      const options = {
        key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || 'rzp_test_YourKeyId', 
        amount: Math.round(paymentData.amount * 100),
        currency: paymentData.currency,
        name: "RazorGrowth AI",
        description: "Test Transaction",
        order_id: paymentData.provider_order_id, 
        handler: async function (response: any) {
          toast.success('Payment successful!');
          router.push(`/orders/${orderData.id}`);
        },
        prefill: {
          name: "Test User",
          email: "test@example.com",
          contact: "9999999999"
        },
        theme: {
          color: "#0f172a"
        }
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', function (response: any){
        toast.error('Payment failed: ' + response.error.description);
      });
      rzp.open();

    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (cartLoading || !quote) {
    return (
      <div className="flex flex-col h-full min-h-screen bg-gray-50">
        <Navbar />
        <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8 flex justify-center items-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 h-full">
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Checkout</h1>
        
        <div className="bg-white border rounded-xl shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">Order Summary</h2>
          <div className="space-y-4 mb-6">
            {quote.items.map((item: any) => (
              <div key={item.id} className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{item.product_name || item.product?.name}</p>
                  <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                </div>
                <p className="font-semibold">₹{item.line_total}</p>
              </div>
            ))}
          </div>
          
          <div className="border-t pt-4 space-y-2">
            <div className="flex justify-between text-gray-600">
              <span>Subtotal</span>
              <span>₹{quote.subtotal_amount}</span>
            </div>
            <div className="flex justify-between text-gray-600">
              <span>Tax</span>
              <span>₹{quote.tax_amount}</span>
            </div>
            <div className="flex justify-between font-bold text-xl pt-2">
              <span>Total</span>
              <span>₹{quote.total_amount}</span>
            </div>
          </div>
        </div>

        {quote.policy_evaluations && quote.policy_evaluations.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl shadow-sm p-6 mb-8">
             <h2 className="text-lg font-semibold text-blue-900 mb-2">Policy Evaluation</h2>
             <ul className="list-disc pl-5 space-y-1 text-sm text-blue-800">
               {quote.policy_evaluations.map((p: any, i: number) => (
                 <li key={i}>{p.policy?.name || 'Policy applied'} - {p.status}</li>
               ))}
             </ul>
          </div>
        )}

        <div className="bg-white border rounded-xl shadow-sm p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Confirm your order</h2>
          <p className="text-sm text-gray-600 mb-4">
            By clicking the button below, you confirm that you have reviewed your order and agree to the policies.
          </p>
          <div className="flex items-center space-x-2 mb-6">
            <input 
              type="checkbox" 
              id="confirm" 
              className="rounded text-primary focus:ring-primary h-5 w-5 border-gray-300"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <label htmlFor="confirm" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              I explicitly confirm this transaction for ₹{quote.total_amount}
            </label>
          </div>
          
          <Button 
            className="w-full h-12 text-lg rounded-full" 
            onClick={confirmAndPay}
            disabled={!confirmed || loading}
          >
            {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : 'Pay with Razorpay Test Mode'}
          </Button>
        </div>
      </main>
    </div>
  );
}
