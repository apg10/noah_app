import { api } from "./apiClient";
import type { CreateOrderPayload, Order } from "../types/noah";

// POST /api/orders/ para crear pedido:contentReference[oaicite:12]{index=12}
export async function createOrder(payload: CreateOrderPayload) {
  const res = await api.post<Order>("/orders/", payload);
  return res.data;
}

// Tracking: GET /api/orders/{order_number}/:contentReference[oaicite:13]{index=13}
export async function getOrderByNumber(orderNumber: string) {
  const res = await api.get<Order>(`/orders/${encodeURIComponent(orderNumber)}/`);
  return res.data;
}
