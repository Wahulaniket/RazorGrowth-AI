import createClient from 'openapi-fetch';
import type { paths } from './schema';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = createClient<paths>({
  baseUrl: API_BASE_URL,
});

apiClient.use({
  onRequest({ request }) {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        request.headers.set('Authorization', `Bearer ${token}`);
      }
      
      const tenantSlug = localStorage.getItem('tenantSlug');
      if (tenantSlug) {
        request.headers.set('X-Tenant-Slug', tenantSlug);
      }
    }
    return request;
  }
});
