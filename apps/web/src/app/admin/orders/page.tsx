'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/apiClient';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadOrders() {
      try {
        const { data, error } = await apiClient.GET('/api/v1/orders' as any); // fallback if not in schema yet
        if (data && (data as any).items) {
          setOrders((data as any).items);
        } else if (Array.isArray(data)) {
          setOrders(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Orders Management</h1>
      </div>

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {loading ? (
          <div className="p-8 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Payment Status</TableHead>
                <TableHead>Total Amount</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.length > 0 ? orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-medium font-mono text-sm">{order.id.slice(0, 8)}...</TableCell>
                  <TableCell>{order.user_id}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">{order.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="capitalize">{order.payment_status}</Badge>
                  </TableCell>
                  <TableCell>
                    {order.currency === 'INR' ? '₹' : order.currency} {order.total_amount}
                  </TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No orders found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
