import { Link } from "@tanstack/react-router";
import { ArrowRight, Bot, ShieldCheck, Zap } from "lucide-react";
import { CustomerShell } from "@/components/layout/CustomerShell";
import { Button } from "@/components/ui/button";

export function HomePage() {
  return (
    <CustomerShell>
      <main>
        <section className="relative overflow-hidden border-b border-rg-line/70 px-5 py-24 md:px-6 md:py-32">
          <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_top_right,rgba(201,160,80,0.08),transparent_50%)]" />
          <div className="relative z-10 mx-auto max-w-[1280px]">
            <p className="rg-kicker text-rg-gold">Next-gen commerce</p>
            <h1 className="mt-6 max-w-[14ch] font-display text-6xl leading-[1.05] tracking-tight text-rg-cream sm:text-7xl md:text-8xl">
              Shop at the speed of thought.
            </h1>
            <p className="mt-8 max-w-[42ch] text-lg leading-relaxed text-rg-cream-dim md:text-xl">
              RazorGrowth AI bridges the gap between intention and action. Explain what you need, and our agent finds, validates, and prepares your order.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Button asChild size="lg" className="h-14 rounded-full bg-rg-gold px-8 text-base font-semibold text-rg-ink hover:bg-rg-gold-soft">
                <Link to="/ai">Start AI Shopping <ArrowRight className="ml-2 size-5" /></Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-14 rounded-full border-rg-line bg-transparent px-8 text-base font-semibold text-rg-cream hover:bg-rg-navy">
                <Link to="/products">Browse catalog</Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-[1280px] gap-px border-x border-rg-line/70 bg-rg-line/70 md:grid-cols-3">
          {[
            { icon: Bot, title: "Intent-driven", desc: "Just describe your needs. The AI understands context and constraints instantly." },
            { icon: ShieldCheck, title: "Policy-bounded", desc: "Every action is validated against merchant policies before execution." },
            { icon: Zap, title: "Frictionless", desc: "From search to checkout, the entire flow is unified and lightning fast." },
          ].map((feature, i) => (
            <div key={i} className="bg-rg-ink p-10 md:p-12">
              <div className="grid size-12 place-items-center rounded-2xl bg-rg-navy text-rg-gold">
                <feature.icon className="size-6" />
              </div>
              <h3 className="mt-6 font-display text-2xl text-rg-cream">{feature.title}</h3>
              <p className="mt-3 leading-relaxed text-rg-cream-dim">{feature.desc}</p>
            </div>
          ))}
        </section>
      </main>
    </CustomerShell>
  );
}
