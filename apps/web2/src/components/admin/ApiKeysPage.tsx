import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { AdminShell } from '@/components/layout/AdminShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Key, Trash2, Plus, AlertCircle, Copy, Check } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

export function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [newKeyName, setNewKeyName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<{ id: string; name: string; secret: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: keys, isLoading } = useQuery({
    queryKey: ['admin-api-keys'],
    queryFn: () => api.get('/api/v1/api-keys'),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => api.post('/api/v1/api-keys', { name }),
    onSuccess: (data) => {
      setGeneratedKey(data);
      setNewKeyName('');
      queryClient.invalidateQueries({ queryKey: ['admin-api-keys'] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-api-keys'] });
    },
  });

  const handleCopy = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <AdminShell title="API Keys">
      <div className="flex flex-col gap-8 max-w-4xl">
        <div className="bg-rg-panel border border-rg-line p-6 rounded-2xl">
          <h3 className="text-lg font-display text-rg-cream mb-2">Generate New Key</h3>
          <p className="text-sm text-rg-cream-dim mb-4">
            Create an API key to allow external agents or services to interact with your catalog.
          </p>
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="keyName" className="sr-only">Key Name</Label>
              <Input
                id="keyName"
                placeholder="e.g. Production Agent Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="bg-rg-ink border-rg-line text-rg-cream"
              />
            </div>
            <Button
              onClick={() => createMutation.mutate(newKeyName)}
              disabled={!newKeyName.trim() || createMutation.isPending}
              className="bg-rg-gold text-rg-ink hover:bg-rg-gold-soft"
            >
              <Plus className="mr-2 size-4" /> Generate
            </Button>
          </div>
        </div>

        <div className="bg-rg-panel border border-rg-line rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-rg-line">
            <h3 className="text-lg font-display text-rg-cream">Active API Keys</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-rg-cream">
              <thead className="bg-rg-navy text-xs uppercase tracking-[0.15em] text-rg-cream-dim">
                <tr>
                  <th className="px-6 py-4 font-medium">Name</th>
                  <th className="px-6 py-4 font-medium">Key Prefix</th>
                  <th className="px-6 py-4 font-medium">Created</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rg-line">
                {isLoading ? (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-rg-cream-dim">Loading keys...</td></tr>
                ) : !keys || keys.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-rg-cream-dim">No API keys found.</td></tr>
                ) : (
                  keys.map((k: any) => (
                    <tr key={k.id} className="hover:bg-rg-navy/30 transition-colors">
                      <td className="px-6 py-4 font-medium">{k.name}</td>
                      <td className="px-6 py-4 font-mono text-rg-cream-dim">{k.prefix}...</td>
                      <td className="px-6 py-4 text-rg-cream-dim">{new Date(k.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4">
                        {k.is_revoked ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400">Revoked</span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">Active</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {!k.is_revoked && (
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                            onClick={() => {
                              if (window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
                                revokeMutation.mutate(k.id);
                              }
                            }}
                          >
                            <Trash2 className="size-4 mr-2" /> Revoke
                          </Button>
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

      <Dialog open={!!generatedKey} onOpenChange={(open) => !open && setGeneratedKey(null)}>
        <DialogContent className="bg-rg-panel border-rg-line text-rg-cream sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-display text-rg-gold flex items-center gap-2">
              <Key className="size-5" /> Key Generated
            </DialogTitle>
            <DialogDescription className="text-rg-cream-dim pt-2">
              Please copy your new API key now. You will <strong className="text-rg-cream">never</strong> be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center space-x-2 mt-4">
            <div className="grid flex-1 gap-2">
              <Label htmlFor="secret" className="sr-only">
                Secret Key
              </Label>
              <Input
                id="secret"
                defaultValue={generatedKey?.secret}
                readOnly
                className="bg-rg-ink border-rg-line font-mono text-sm text-rg-cream"
              />
            </div>
            <Button size="sm" className="px-3 bg-rg-navy hover:bg-rg-line text-rg-cream" onClick={handleCopy}>
              <span className="sr-only">Copy</span>
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="mt-6 flex items-center gap-2 p-3 bg-amber-500/10 rounded-lg text-amber-200/90 text-sm">
            <AlertCircle className="size-5 shrink-0" />
            <p>Make sure to store this securely. We do not store the unhashed secret on our servers.</p>
          </div>
          <div className="mt-4 flex justify-end">
             <Button onClick={() => setGeneratedKey(null)} className="bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
                I've copied it
             </Button>
          </div>
        </DialogContent>
      </Dialog>
    </AdminShell>
  );
}
