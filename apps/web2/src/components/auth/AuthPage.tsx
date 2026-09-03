import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Brand } from "@/components/layout/CustomerShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { authStore } from "@/lib/auth-store";
import { toast } from "sonner";

export function AuthPage({ register = false }: { register?: boolean }) {
  const [mode, setMode] = useState(register);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode) {
        // Register
        await api.post("/api/v1/auth/register", {
          email,
          password,
          full_name: name,
        });
        toast.success("Account created! Please sign in.");
        setMode(false);
      } else {
        // Login
        const data = await api.post("/api/v1/auth/login", {
          email,
          password,
        });
        
        // Fetch tenants for the user to get tenantId
        const { access_token } = data;
        
        const tenantData = await api.get("/api/v1/users/me/tenants", {
          headers: { Authorization: `Bearer ${access_token}` },
        });

        const tenantId = tenantData.memberships[0]?.tenant_id || "";
        
        authStore.setAuth(access_token, tenantId, tenantData);
        toast.success("Signed in successfully");
        navigate({ to: "/" });
      }
    } catch (error: any) {
      toast.error(error.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rg-page flex min-h-screen items-center justify-center px-5 py-10">
      <div className="w-full max-w-md">
        <Brand />
        <div className="mt-10 rounded-2xl border border-rg-line bg-rg-panel p-7">
          <p className="rg-kicker">{mode ? "Create account" : "Welcome back"}</p>
          <h1 className="mt-3 font-display text-5xl">{mode ? "Join RazorGrowth." : "Sign in to shop."}</h1>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {mode && (
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
              {loading ? "Please wait..." : mode ? "Create account" : "Sign in"}
            </Button>
            {!mode && (
              <button type="button" className="w-full text-xs text-rg-gold underline">
                Forgot password?
              </button>
            )}
          </form>
          <button
            onClick={() => setMode(!mode)}
            className="mt-7 w-full text-sm text-rg-cream-dim"
          >
            {mode ? "Already have an account? Sign in" : "New to RazorGrowth? Create an account"}
          </button>
        </div>
        <Link to="/" className="mt-6 block text-center text-sm text-rg-cream-dim">
          ← Return to storefront
        </Link>
      </div>
    </div>
  );
}
