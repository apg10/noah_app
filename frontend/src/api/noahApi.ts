// src/api/noahApi.ts
import { apiClient as api } from "./apiClient";
import { endpoints } from "./endpoints";
import type { MenuCategory, MenuItem, CreateOrderPayload, Order } from "../types/noah";

// Si todavía no tienes Restaurant en types/noah.ts, lo dejamos aquí PERO sin mezclar con CreateOrderPayload
export type Restaurant = {
  id: number;
  name: string;
  slug: string;
  phone?: string;
  address?: string;
  delivery_base_fee_cop?: number;
  daily_order_limit?: number;
  is_active: boolean;
};

export async function listRestaurants() {
  const { data } = await api.get<Restaurant[]>(endpoints.restaurants());
  return data;
}

export async function listCategories(restaurantId: number) {
  const { data } = await api.get<MenuCategory[]>(endpoints.categories(), {
    params: { restaurant: restaurantId },
  });
  return data;
}

export async function listMenuItems(restaurantId: number) {
  const { data } = await api.get<MenuItem[]>(endpoints.menuItems(), {
    params: { restaurant: restaurantId },
  });
  return data;
}

export async function createOrder(payload: CreateOrderPayload) {
  const { data } = await api.post<Order>(endpoints.orders(), payload);
  return data;
}

export async function getOrderByNumber(orderNumber: string) {
  const { data } = await api.get<Order>(endpoints.orderByNumber(orderNumber));
  return data;
}
