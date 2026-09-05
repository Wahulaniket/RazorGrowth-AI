export interface User {
  id: string;
  email: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TenantMembership {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export interface UserWithTenants extends User {
  tenants: TenantMembership[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Product {
  id: string;
  name: string;
  description: string | null;
  price: number;
  currency: string;
  stock: number;
  tenant_id: string;
  category_id: string | null;
  is_active: boolean;
  sku: string | null;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: string | null;
  tenant_id: string;
}

export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  product: Product;
}

export interface Cart {
  id: string;
  tenant_id: string;
  user_id: string;
  status: string;
  items: CartItem[];
  total_amount: number;
  created_at: string;
  updated_at: string;
}

export interface CheckoutQuoteResponse {
  id: string;
  cart_id: string;
  tenant_id: string;
  total_amount: number;
  currency: string;
  expires_at: string;
}

export interface Order {
  id: string;
  tenant_id: string;
  user_id: string;
  status: string;
  total_amount: number;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentResponse {
  id: string;
  order_id: string;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_id: string | null;
}
