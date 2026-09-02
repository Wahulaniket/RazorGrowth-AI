import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Outlet, Link, createRootRouteWithContext, useRouter, HeadContent, Scripts } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return <div className="rg-page flex min-h-screen items-center justify-center px-6"><div className="max-w-md text-center"><p className="rg-kicker">404 / unavailable</p><h1 className="mt-4 font-display text-6xl text-rg-cream">Page not found</h1><p className="mt-4 text-rg-cream-dim">The destination you requested does not exist or has moved.</p><Link to="/" className="mt-7 inline-flex rounded-full bg-rg-gold px-5 py-3 text-sm font-semibold text-rg-ink">Return home</Link></div></div>;
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => { reportLovableError(error, { boundary: "tanstack_root_error_component" }); }, [error]);
  return <div className="rg-page flex min-h-screen items-center justify-center px-6"><div className="max-w-md text-center"><p className="rg-kicker">500 / service interruption</p><h1 className="mt-4 font-display text-5xl text-rg-cream">This page didn’t load</h1><p className="mt-4 text-rg-cream-dim">Something went wrong. Try again or return to the storefront.</p><div className="mt-7 flex justify-center gap-3"><button onClick={() => { router.invalidate(); reset(); }} className="rounded-full bg-rg-gold px-5 py-3 text-sm font-semibold text-rg-ink">Try again</button><a href="/" className="rounded-full border border-rg-line px-5 py-3 text-sm font-semibold text-rg-cream">Go home</a></div></div></div>;
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "RazorGrowth AI" },
      { name: "description", content: "Explainable AI commerce for customers and growth intelligence for merchants." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [{ rel: "stylesheet", href: appCss }, { rel: "icon", href: "/favicon.ico", type: "image/x-icon" }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return <html lang="en"><head><HeadContent /></head><body>{children}<Scripts /></body></html>;
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return <QueryClientProvider client={queryClient}><Outlet /></QueryClientProvider>;
}