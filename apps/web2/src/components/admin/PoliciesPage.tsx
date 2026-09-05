import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { AdminShell } from '@/components/layout/AdminShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Shield } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

export function PoliciesPage() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [maxAmount, setMaxAmount] = useState('10000');

  const { data: policies, isLoading } = useQuery({
    queryKey: ['admin-policies'],
    queryFn: () => api.get('/api/v1/policies'),
  });

  const createMutation = useMutation({
    mutationFn: (amount: number) => api.post('/api/v1/policies', {
      name: `Require Confirmation over ₹${amount}`,
      policy_type: 'CHECKOUT_VALIDATION',
      level: 'MERCHANT',
      is_active: true,
      rules: {
        require_confirmation: true,
        max_amount: amount,
        currency: 'INR'
      }
    }),
    onSuccess: () => {
      setIsDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['admin-policies'] });
    },
  });

  return (
    <AdminShell title="Policies">
      <div className="flex flex-col gap-8 max-w-5xl">
        <div className="flex justify-between items-center bg-rg-panel border border-rg-line p-6 rounded-2xl">
          <div>
            <h3 className="text-lg font-display text-rg-cream flex items-center gap-2">
              <Shield className="size-5 text-rg-gold" /> Commerce Rules
            </h3>
            <p className="text-sm text-rg-cream-dim mt-1">
              Configure automated policies for cart validation and checkout constraints.
            </p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
                <Plus className="mr-2 size-4" /> New Policy
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-rg-panel border-rg-line text-rg-cream">
              <DialogHeader>
                <DialogTitle>Create High-Value Policy</DialogTitle>
                <DialogDescription className="text-rg-cream-dim">
                  Require manual quote confirmation for orders exceeding a certain amount.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="maxAmount">Amount Threshold (₹)</Label>
                  <Input 
                    id="maxAmount" 
                    type="number" 
                    value={maxAmount} 
                    onChange={(e) => setMaxAmount(e.target.value)} 
                    className="bg-rg-ink border-rg-line text-rg-cream"
                  />
                </div>
                <div className="pt-2 flex justify-end">
                  <Button 
                    onClick={() => createMutation.mutate(parseFloat(maxAmount))}
                    disabled={createMutation.isPending || !maxAmount}
                    className="bg-rg-gold text-rg-ink hover:bg-rg-gold-soft"
                  >
                    {createMutation.isPending ? 'Saving...' : 'Create Policy'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="bg-rg-panel border border-rg-line rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-rg-cream">
              <thead className="bg-rg-navy text-xs uppercase tracking-[0.15em] text-rg-cream-dim">
                <tr>
                  <th className="px-6 py-4 font-medium">Name</th>
                  <th className="px-6 py-4 font-medium">Type</th>
                  <th className="px-6 py-4 font-medium">Rules</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rg-line">
                {isLoading ? (
                  <tr><td colSpan={4} className="px-6 py-8 text-center text-rg-cream-dim">Loading policies...</td></tr>
                ) : !policies || policies.length === 0 ? (
                  <tr><td colSpan={4} className="px-6 py-8 text-center text-rg-cream-dim">No active policies.</td></tr>
                ) : (
                  policies.map((p: any) => (
                    <tr key={p.id} className="hover:bg-rg-navy/30 transition-colors">
                      <td className="px-6 py-4 font-medium">{p.name}</td>
                      <td className="px-6 py-4"><span className="text-xs bg-rg-ink px-2 py-1 rounded border border-rg-line">{p.policy_type}</span></td>
                      <td className="px-6 py-4 font-mono text-xs text-rg-cream-dim">
                        {JSON.stringify(p.rules)}
                      </td>
                      <td className="px-6 py-4">
                        {p.is_active ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">Active</span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-rg-line text-rg-cream-dim">Disabled</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
