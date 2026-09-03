import { Check } from "lucide-react";
import React from "react";

export function Status({ children, tone = "success" }: { children: React.ReactNode; tone?: "success" | "warning" | "error" | "neutral" }) {
  const styles = {
    success: "bg-rg-success/15 text-rg-success border-rg-success/25",
    warning: "bg-rg-warning/15 text-rg-warning border-rg-warning/25",
    error: "bg-rg-error/15 text-rg-error border-rg-error/25",
    neutral: "bg-rg-navy text-rg-cream-dim border-rg-line"
  };
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-medium ${styles[tone]}`}>{children}</span>;
}

export function TrustStrip() {
  return (
    <div className="flex flex-wrap gap-x-6 gap-y-2 text-[10px] uppercase tracking-[0.18em] text-rg-cream-dim">
      <span className="flex items-center gap-2"><Check className="size-3 text-rg-success" /> Policy-controlled</span>
      <span className="flex items-center gap-2"><Check className="size-3 text-rg-success" /> User-confirmed</span>
      <span className="flex items-center gap-2"><Check className="size-3 text-rg-success" /> Full audit trail</span>
    </div>
  );
}

export const money = (value: number) => "₹" + value.toLocaleString("en-IN");
