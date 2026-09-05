import { useState } from "react";
import { Link, useNavigate, useRouter } from "@tanstack/react-router";
import { Brand } from "@/components/layout/CustomerShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, APIError } from "@/lib/api-client";
import { authStore } from "@/lib/auth-store";
import { toast } from "sonner";
import type { UserWithTenants, TenantMembership } from "@/types/api";

export function AuthPage({ register = false }: { register?: boolean }) {
  const [mode, setMode] = useState<'login' | 'register' | 'tenant-select'>(register ? 'register' : 'login');
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  
  const [tempToken, setTempToken] = useState("");
  const [tenantData, setTenantData] = useState<UserWithTenants | null>(null);
  
  const navigate = useNavigate();
  const router = useRouter();

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'register') {
        await api.post("/api/v1/auth/register", {
          email,
          password,
          name,
        });
        toast.success("Account created! Please sign in.");
        setMode('login');
      } else if (mode === 'login') {
        const data = await api.post("/api/v1/auth/login", {
          email,
          password,
        });
        
        const { access_token } = data;
        
        const fetchedTenantData = await api.get("/api/v1/users/me/tenants", {
          headers: { Authorization: `Bearer ${access_token}` },
        });

        if (!fetchedTenantData.tenants || fetchedTenantData.tenants.length === 0) {
          toast.error("No tenants available for this user.");
          return;
        }

        if (fetchedTenantData.tenants.length === 1) {
          // Auto select single tenant
          const tenantId = fetchedTenantData.tenants[0].id;
          authStore.setAuth(access_token, tenantId, fetchedTenantData);
          toast.success("Signed in successfully");
          await router.invalidate();
          await navigate({ to: "/" });
        } else {
          // Show tenant selection
          setTempToken(access_token);
          setTenantData(fetchedTenantData);
          setMode('tenant-select');
        }
      }
    } catch (error: any) {
      const msg = error instanceof APIError ? error.message : "Authentication failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleTenantSelect = async (tenantId: string) => {
    authStore.setAuth(tempToken, tenantId, tenantData);
    toast.success("Signed in successfully");
    await router.invalidate();
    await navigate({ to: "/" });
  };

  if (mode === 'tenant-select' && tenantData) {
    return (
      <div className="rg-page flex min-h-screen items-center justify-center px-5 py-10">
        <div className="w-full max-w-md">
          <Brand />
          <div className="mt-10 rounded-2xl border border-rg-line bg-rg-panel p-7">
            <p className="rg-kicker">Select Workspace</p>
            <h1 className="mt-3 font-display text-4xl">Choose your tenant</h1>
            <div className="mt-8 space-y-3">
              {tenantData.tenants.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleTenantSelect(t.id)}
                  className="w-full rounded-xl border border-rg-line bg-rg-navy p-4 text-left transition-colors hover:border-rg-gold hover:bg-rg-navy/80"
                >
                  <p className="font-semibold text-rg-cream">{t.name}</p>
                  <p className="text-sm text-rg-cream-dim">Role: {t.role}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rg-page flex min-h-screen items-center justify-center px-5 py-10">
      <div className="w-full max-w-md">
        <Brand />
        <div className="mt-10 rounded-2xl border border-rg-line bg-rg-panel p-7">
          <p className="rg-kicker">{mode === 'register' ? "Create account" : "Welcome back"}</p>
          <h1 className="mt-3 font-display text-5xl">{mode === 'register' ? "Join RazorGrowth." : "Sign in to shop."}</h1>
          <form className="mt-8 space-y-5" onSubmit={handleLoginSubmit}>
            {mode === 'register' && (
              <label className="block text-sm text-rg-cream-dim">
                Full Name
                <Input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-2 h-11 border-rg-line bg-rg-navy text-rg-cream"
                />
              </label>
            )}
            <label className="block text-sm text-rg-cream-dim">
              Email
              <Input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 h-11 border-rg-line bg-rg-navy text-rg-cream"
              />
            </label>
            <label className="block text-sm text-rg-cream-dim">
              Password
              <Input
                required
                minLength={8}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 h-11 border-rg-line bg-rg-navy text-rg-cream"
              />
            </label>
            <Button
              className="w-full rounded-full bg-rg-gold py-3 text-rg-ink hover:bg-rg-gold-soft"
              type="submit"
              disabled={loading}
            >
              {loading ? "Please wait..." : mode === 'register' ? "Create account" : "Sign in"}
            </Button>
            {mode === 'login' && (
              <button type="button" className="w-full text-xs text-rg-gold underline">
                Forgot password?
              </button>
            )}
          </form>
          <button
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="mt-7 w-full text-sm text-rg-cream-dim"
          >
            {mode === 'login' ? "New to RazorGrowth? Create an account" : "Already have an account? Sign in"}
          </button>
        </div>
        <Link to="/" className="mt-6 block text-center text-sm text-rg-cream-dim">
          ← Return to storefront
        </Link>
      </div>
    </div>
  );
}

