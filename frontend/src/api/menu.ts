import { apiClient as api } from "./apiClient";
import type { MenuCategory, MenuItem } from "../types/noah";

const RESTAURANT_ID = Number(import.meta.env.VITE_RESTAURANT_ID || 1);

// Nota: en docs aparece en distintas formas según el módulo.
// - /api/menu-categories/ y /api/menu-items/:contentReference[oaicite:9]{index=9}
// - /api/categories/?restaurant= y /api/menu-items/?restaurant=:contentReference[oaicite:10]{index=10}
// - /api/menu/items/:contentReference[oaicite:11]{index=11}
async function tryGet<T>(paths: string[]): Promise<T> {
  let lastErr: unknown = null;

  for (const p of paths) {
    try {
      const res = await api.get<T>(p);
      return res.data;
    } catch (e) {
      lastErr = e;
    }
  }

  throw lastErr;
}

export async function getCategories(restaurantId = RESTAURANT_ID) {
  return tryGet<MenuCategory[]>([
    `/menu-categories/?restaurant=${restaurantId}`,
    `/categories/?restaurant=${restaurantId}`,
  ]);
}

export async function getMenuItems(restaurantId = RESTAURANT_ID) {
  return tryGet<MenuItem[]>([
    `/menu-items/?restaurant=${restaurantId}`,
    `/menu/items/?restaurant=${restaurantId}`,
    `/menu/items/`,
  ]);
}
