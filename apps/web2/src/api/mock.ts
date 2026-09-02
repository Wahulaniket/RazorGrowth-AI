import type { Analytics, CartItem, Order, Product, Recommendation } from "./types";

const products: Product[] = [
  { id: "aurelia-travel", name: "Aurelia Travel Headphones", category: "Audio", description: "Noise-isolating wireless headphones with 38-hour battery life and a fold-flat design.", price: 8499, rating: 4.8, availability: "In stock", inventory: 24, image: "hero", reason: "Under your ₹10,000 budget, lightweight, and designed to fold flat for travel." },
  { id: "meridian-14", name: "Meridian 14 Pro", category: "Computing", description: "A quiet, long-lasting ultrabook tuned for creative work and programming on the move.", price: 112900, rating: 4.7, availability: "Low stock", inventory: 6, image: "hero", reason: "18-hour battery and quiet thermals make it a strong travel-day companion." },
  { id: "aperture-x5", name: "Aperture X5", category: "Mobile", description: "Flagship photography phone with a 1-inch sensor and pro-grade night capture.", price: 89999, rating: 4.9, availability: "In stock", inventory: 18, image: "hero", reason: "A large sensor and optical stabilization fit a photography-first brief." },
  { id: "lumen-27", name: "Lumen 27 QD", category: "Displays", description: "A vivid 165Hz quantum-dot monitor with a fast 1ms response time.", price: 46999, rating: 4.6, availability: "In stock", inventory: 31, image: "hero", reason: "Fast refresh and crisp color make it a balanced gaming setup upgrade." },
  { id: "vector-16", name: "Vector Pro 16", category: "Computing", description: "A 32GB performance laptop built for long compile sessions and deep work.", price: 124990, rating: 4.8, availability: "In stock", inventory: 12, image: "hero", reason: "High-memory configuration keeps demanding development workflows responsive." },
  { id: "orbit-speaker", name: "Orbit Home Speaker", category: "Audio", description: "Room-filling wireless sound with adaptive listening modes.", price: 12999, rating: 4.5, availability: "Low stock", inventory: 4, image: "hero", reason: "A compact footprint and adaptive audio make it an easy room upgrade." },
];

let cart: CartItem[] = [{ ...products[0], quantity: 1, variant: "Midnight" }];
let orders: Order[] = [{ id: "RG-48213", date: "12 Sep 2026", total: 8499, paymentStatus: "Paid", status: "Shipped", items: [cart[0]], address: "12 Palm Avenue, Mumbai, Maharashtra 400001" }];

export const mockCatalog = {
  list: (query = "") => products.filter((product) => `${product.name} ${product.category}`.toLowerCase().includes(query.toLowerCase())),
  get: (id: string) => products.find((product) => product.id === id) ?? products[0],
  recommendations: (): Recommendation[] => products.slice(0, 3).map((product, index) => ({ ...product, confidence: `${96 - index * 4}% match` })),
};

export const mockCart = {
  get: () => cart,
  add: (product: Product, quantity = 1) => { const existing = cart.find((item) => item.id === product.id); cart = existing ? cart.map((item) => item.id === product.id ? { ...item, quantity: item.quantity + quantity } : item) : [...cart, { ...product, quantity, variant: "Midnight" }]; return cart; },
  update: (id: string, quantity: number) => { cart = quantity < 1 ? cart.filter((item) => item.id !== id) : cart.map((item) => item.id === id ? { ...item, quantity } : item); return cart; },
  remove: (id: string) => { cart = cart.filter((item) => item.id !== id); return cart; },
  validate: () => ({ ok: true, message: "Inventory and policy checks passed." }),
};

export const mockOrders = {
  list: () => orders,
  get: (id: string) => orders.find((order) => order.id === id) ?? orders[0],
  create: (address: string) => { const current = cart; const order: Order = { id: `RG-${48214 + orders.length}`, date: "18 Sep 2026", total: current.reduce((sum, item) => sum + item.price * item.quantity, 0), paymentStatus: "Paid", status: "Processing", items: current, address }; orders = [order, ...orders]; cart = []; return order; },
};

export const mockAdmin = {
  analytics: (): Analytics => ({ revenue: 4280000, orders: 3912, customers: 2840, conversion: 4.7, averageOrderValue: 1535 }),
};