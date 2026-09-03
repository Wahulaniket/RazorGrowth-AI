import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Check, ChevronLeft, CircleAlert, CreditCard, ArrowRight } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { OrderSummary } from "@/components/cart/OrderSummary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

export function CheckoutPage() {
  const [step, setStep] = useState(1);
  const [address, setAddress] = useState({ name: "", email: "", phone: "", line: "", city: "", state: "", postal: "" });
  const [error, setError] = useState("");
  const [quoteId, setQuoteId] = useState<string | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  
  const navigate = useNavigate();

  const { data: cart } = useQuery({
    queryKey: ['cart'],
    queryFn: async () => api.get("/api/v1/cart/"),
  });

  const quoteMutation = useMutation({
    mutationFn: async () => api.post("/api/v1/checkout/quote", {
      shipping_address: `${address.line}, ${address.city}, ${address.state} ${address.postal}`,
      billing_address: `${address.line}, ${address.city}, ${address.state} ${address.postal}`
    }),
    onSuccess: (data) => {
      setQuoteId(data.id);
      setStep(4);
      setError("");
    },
    onError: (err: any) => {
      setError(err.data?.detail || "Failed to create quote");
    }
  });

  const confirmMutation = useMutation({
    mutationFn: async () => api.post(`/api/v1/checkout/${quoteId}/confirm`, {}),
    onSuccess: (data) => {
      setOrderId(data.id);
      paymentMutation.mutate(data.id);
    },
    onError: (err: any) => {
      setError(err.data?.detail || "Failed to confirm order");
    }
  });

  const paymentMutation = useMutation({
    mutationFn: async (oId: string) => api.post("/api/v1/payments", {
      order_id: oId,
      amount: cart?.total || 0,
      currency: "INR",
      provider: "fake",
      provider_payment_id: "fake_" + Math.random().toString(36).substring(7)
    }),
    onSuccess: () => {
      setStep(5);
      setTimeout(() => {
        if (orderId) {
          navigate({ to: "/orders/$id", params: { id: orderId } });
        }
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.data?.detail || "Payment failed");
    }
  });

  const steps = ["Customer", "Shipping", "Review", "Payment", "Result"];
  const items = cart?.items || [];

  const submit = () => {
    if (step === 1 && (!address.name || !address.email || !address.phone)) {
      setError("Please complete the customer details.");
      return;
    }
    if (step === 2 && (!address.line || !address.city || !address.postal)) {
      setError("Please complete the shipping details.");
      return;
    }
    setError("");

    if (step === 3) {
      // Create quote
      quoteMutation.mutate();
      return;
    }

    if (step === 4) {
      // Confirm quote & pay
      confirmMutation.mutate();
      return;
    }

    setStep(step + 1);
  };

  return (
    <CustomerShell>
      <main className="mx-auto max-w-[1100px] px-5 py-10 md:px-6">
        <p className="rg-kicker">Secure checkout / backend-authoritative</p>
        <h1 className="mt-3 font-display text-5xl text-rg-cream">Complete your order.</h1>
        <div className="mt-8 grid grid-cols-5 gap-2">
          {steps.map((label, index) => (
            <div key={label} className={`border-t-2 pt-3 text-xs ${index + 1 <= step ? "border-rg-gold text-rg-gold-soft" : "border-rg-line text-rg-cream-dim"}`}>
              <span className="font-semibold">0{index + 1}</span>
              <span className="ml-2 hidden sm:inline">{label}</span>
            </div>
          ))}
        </div>
        
        {error && (
          <div role="alert" className="mt-6 flex items-center gap-2 rounded-xl border border-rg-error/30 bg-rg-error/10 p-4 text-sm text-rg-error">
            <CircleAlert className="size-4" />{error}
          </div>
        )}
        
        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_360px]">
          <section className="rounded-2xl border border-rg-line bg-rg-panel p-6 md:p-8">
            {step === 1 && (
              <>
                <h2 className="font-display text-3xl">Customer details</h2>
                <div className="mt-6 grid gap-5 sm:grid-cols-2">
                  {[["name", "Name"], ["email", "Email"], ["phone", "Phone"]].map(([key, label]) => (
                    <label key={key} className="text-sm text-rg-cream-dim sm:last:col-span-2">
                      {label}
                      <Input value={address[key as keyof typeof address]} onChange={(e) => setAddress({ ...address, [key]: e.target.value })} className="mt-2 h-11 border-rg-line bg-rg-navy text-rg-cream" type={key === "email" ? "email" : "text"} />
                    </label>
                  ))}
                </div>
              </>
            )}
            
            {step === 2 && (
              <>
                <h2 className="font-display text-3xl">Shipping address</h2>
                <div className="mt-6 grid gap-5 sm:grid-cols-2">
                  {[["line", "Address"], ["city", "City"], ["state", "State"], ["postal", "Postal code"]].map(([key, label]) => (
                    <label key={key} className="text-sm text-rg-cream-dim">
                      {label}
                      <Input value={address[key as keyof typeof address]} onChange={(e) => setAddress({ ...address, [key]: e.target.value })} className="mt-2 h-11 border-rg-line bg-rg-navy text-rg-cream" />
                    </label>
                  ))}
                </div>
              </>
            )}
            
            {step === 3 && (
              <>
                <h2 className="font-display text-3xl">Review your order</h2>
                <div className="mt-6 rounded-xl border border-rg-line p-4 text-sm text-rg-cream-dim">
                  {address.name} · {address.email}<br />{address.line}, {address.city}, {address.state} {address.postal}
                </div>
              </>
            )}
            
            {step === 4 && (
              <>
                <h2 className="font-display text-3xl">Payment</h2>
                <p className="mt-3 text-sm leading-relaxed text-rg-cream-dim">Using the configured provider abstraction for this demo. The backend will verify payment status before marking the order as paid.</p>
                <div className="mt-6 rounded-xl border border-rg-gold/30 bg-rg-gold/10 p-5">
                  <div className="flex items-center gap-3">
                    <CreditCard className="size-5 text-rg-gold" />
                    <div>
                      <p className="font-semibold text-rg-cream">FakePaymentProvider</p>
                      <p className="text-xs text-rg-cream-dim">Local / CI test mode</p>
                    </div>
                  </div>
                </div>
              </>
            )}
            
            {step === 5 && (
              <div className="text-center">
                <Check className="mx-auto size-10 text-rg-success" />
                <h2 className="mt-4 font-display text-4xl">Payment received</h2>
                <p className="mt-2 text-sm text-rg-cream-dim">Your order status is now being confirmed by the backend.</p>
              </div>
            )}
            
            <div className="mt-8 flex justify-between gap-3">
              {step > 1 && step < 5 && (
                <Button variant="outline" className="rounded-full border-rg-line bg-transparent text-rg-cream" onClick={() => setStep(step - 1)}>
                  <ChevronLeft /> Back
                </Button>
              )}
              {step < 5 && (
                <Button 
                  className="ml-auto rounded-full bg-rg-gold text-rg-ink hover:bg-rg-gold-soft" 
                  onClick={submit}
                  disabled={quoteMutation.isPending || confirmMutation.isPending || paymentMutation.isPending}
                >
                  {step === 4 ? "Pay securely" : "Continue"}
                  <ArrowRight />
                </Button>
              )}
            </div>
          </section>
          
          <aside>
            <OrderSummary items={items} />
          </aside>
        </div>
      </main>
    </CustomerShell>
  );
}
