export { mockAdmin, mockCart, mockCatalog, mockOrders } from "./mock";
export type * from "./types";

export const apiConfig = {
  baseUrl: import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:8000",
  mode: "mock" as "mock" | "fastapi",
};

export const backendContract = {
  auth: { login: "/api/v1/auth/login", register: "/api/v1/auth/register", me: "/api/v1/auth/me" },
  catalog: { search: "/api/v1/catalog/search", product: "/api/v1/catalog/products/{product_id}" },
  agent: { chat: "/api/v1/agent/chat" },
  cart: { get: "BACKEND_CONTRACT_REQUIRED", add: "BACKEND_CONTRACT_REQUIRED", update: "BACKEND_CONTRACT_REQUIRED", remove: "BACKEND_CONTRACT_REQUIRED", validate: "BACKEND_CONTRACT_REQUIRED" },
  checkout: { order: "BACKEND_CONTRACT_REQUIRED", payment: "BACKEND_CONTRACT_REQUIRED", status: "BACKEND_CONTRACT_REQUIRED" },
};