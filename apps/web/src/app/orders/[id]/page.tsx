'use client';

import { Navbar } from '@/components/navbar';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export default function OrderConfirmationPage({ params }: { params: { id: string } }) {
  // We can fetch order details using the ID if we have an endpoint for it
  // For now, we'll just display a success message with the ID

  return (
    <div className="flex flex-col h-full min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-16 flex flex-col items-center justify-center">
        <div className="bg-white border rounded-2xl shadow-lg p-10 text-center w-full">
          <div className="flex justify-center mb-6">
            <CheckCircle2 className="h-20 w-20 text-green-500" />
          </div>
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Order Confirmed!</h1>
          <p className="text-lg text-gray-600 mb-8">
            Thank you for your purchase. Your order <span className="font-semibold text-gray-900">#{params.id}</span> is being processed.
          </p>
          
          <div className="space-y-4">
            <Link href="/">
              <Button className="w-full h-12 text-lg rounded-full" variant="outline">
                Continue Shopping
              </Button>
            </Link>
            <Link href="/admin/orders">
              <Button className="w-full h-12 text-lg rounded-full" variant="ghost">
                View in Merchant Dashboard <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
