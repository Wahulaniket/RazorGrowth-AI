export type Product = {
  id: string;
  name: string;
  category: string;
  description: string;
  price: number;
  rating: number;
  availability: "In stock" | "Low stock" | "Out of stock";
  inventory: number;
  image: string;
  reason: string;
};

export type CartItem = Product & { quantity: number; variant: string };

export type Order = {
  id: string;
  date: string;
  total: number;
  paymentStatus: "Paid" | "Pending" | "Failed";
  status: "Processing" | "Shipped" | "Delivered" | "Cancelled";
  items: CartItem[];
  address: string;
};

export type Recommendation = Product & { confidence: string };

export type Analytics = {
  revenue: number;
  orders: number;
  customers: number;
  conversion: number;
  averageOrderValue: number;
};

export type APIError = { status: number; message: string };