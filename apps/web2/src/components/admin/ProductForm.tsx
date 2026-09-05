import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { api } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { AdminShell } from '@/components/layout/AdminShell';

const productSchema = z.object({
  sku: z.string().min(1, 'SKU is required').max(100),
  name: z.string().min(2, 'Name must be at least 2 characters').max(255),
  slug: z.string().min(2, 'Slug must be at least 2 characters').max(255),
  description: z.string().optional(),
  category_id: z.string().uuid('Category ID is required'),
  brand: z.string().max(255).optional(),
  base_price: z.coerce.number().positive('Price must be greater than 0'),
  currency: z.string().min(3).max(3).default('INR'),
});

type ProductFormData = z.infer<typeof productSchema>;

export function ProductForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      sku: '',
      name: '',
      slug: '',
      description: '',
      category_id: '00000000-0000-0000-0000-000000000000', // Dummy UUID for now, in a real app this would be a select
      brand: '',
      base_price: 0,
      currency: 'INR',
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ProductFormData) => api.post('/api/v1/products', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
      navigate({ to: '/admin/products' });
    },
  });

  const onSubmit = (data: ProductFormData) => {
    mutation.mutate(data);
  };

  return (
    <AdminShell title="New Product">
      <div className="max-w-2xl mt-6">
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Product Name</Label>
            <Input id="name" {...form.register('name')} placeholder="e.g. Premium Widget" className="bg-rg-panel border-rg-line text-rg-cream" />
            {form.formState.errors.name && <p className="text-red-500 text-sm">{form.formState.errors.name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sku">SKU</Label>
              <Input id="sku" {...form.register('sku')} placeholder="WIDGET-001" className="bg-rg-panel border-rg-line text-rg-cream" />
              {form.formState.errors.sku && <p className="text-red-500 text-sm">{form.formState.errors.sku.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">Slug</Label>
              <Input id="slug" {...form.register('slug')} placeholder="premium-widget" className="bg-rg-panel border-rg-line text-rg-cream" />
              {form.formState.errors.slug && <p className="text-red-500 text-sm">{form.formState.errors.slug.message}</p>}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" {...form.register('description')} placeholder="A highly premium widget." className="bg-rg-panel border-rg-line text-rg-cream h-24" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="base_price">Base Price</Label>
              <Input id="base_price" type="number" step="0.01" {...form.register('base_price')} className="bg-rg-panel border-rg-line text-rg-cream" />
              {form.formState.errors.base_price && <p className="text-red-500 text-sm">{form.formState.errors.base_price.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="brand">Brand</Label>
              <Input id="brand" {...form.register('brand')} placeholder="Acme Corp" className="bg-rg-panel border-rg-line text-rg-cream" />
            </div>
          </div>
          
          <div className="space-y-2">
              <Label htmlFor="category_id">Category ID (UUID)</Label>
              <Input id="category_id" {...form.register('category_id')} placeholder="00000000-0000-0000-0000-000000000000" className="bg-rg-panel border-rg-line text-rg-cream" />
              {form.formState.errors.category_id && <p className="text-red-500 text-sm">{form.formState.errors.category_id.message}</p>}
          </div>

          <div className="pt-4 flex gap-4">
            <Button type="button" variant="outline" onClick={() => navigate({ to: '/admin/products' })} className="border-rg-line text-rg-cream hover:bg-rg-navy">
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending} className="bg-rg-gold text-rg-ink hover:bg-rg-gold-soft">
              {mutation.isPending ? 'Saving...' : 'Create Product'}
            </Button>
          </div>
          {mutation.isError && (
            <p className="text-red-500 text-sm mt-2">Error creating product: {(mutation.error as any).message}</p>
          )}
        </form>
      </div>
    </AdminShell>
  );
}
