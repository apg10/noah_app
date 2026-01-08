import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CartItem, MenuItem } from "../types/noah";

type CartState = {
  items: CartItem[];
  addItem: (item: MenuItem, qty?: number) => void;
  increase: (menu_item_id: number) => void;
  decrease: (menu_item_id: number) => void;
  remove: (menu_item_id: number) => void;
  clear: () => void;

  subtotal: () => number;
  count: () => number;
};

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (item, qty = 1) => {
        set((state) => {
          const existing = state.items.find((i) => i.menu_item_id === item.id);
          if (existing) {
            const next = state.items.map((i) =>
              i.menu_item_id === item.id
                ? {
                    ...i,
                    quantity: i.quantity + qty,
                    line_total_cop: (i.quantity + qty) * i.unit_price_cop,
                  }
                : i
            );
            return { items: next };
          }

          return {
            items: [
              ...state.items,
              {
                menu_item_id: item.id,
                name: item.name,
                unit_price_cop: item.price_cop,
                quantity: qty,
                line_total_cop: qty * item.price_cop,
              },
            ],
          };
        });
      },

      increase: (id) =>
        set((state) => ({
          items: state.items.map((i) =>
            i.menu_item_id === id
              ? {
                  ...i,
                  quantity: i.quantity + 1,
                  line_total_cop: (i.quantity + 1) * i.unit_price_cop,
                }
              : i
          ),
        })),

      decrease: (id) =>
        set((state) => {
          const target = state.items.find((i) => i.menu_item_id === id);
          if (!target) return state;

          if (target.quantity <= 1) {
            return { items: state.items.filter((i) => i.menu_item_id !== id) };
          }

          return {
            items: state.items.map((i) =>
              i.menu_item_id === id
                ? {
                    ...i,
                    quantity: i.quantity - 1,
                    line_total_cop: (i.quantity - 1) * i.unit_price_cop,
                  }
                : i
            ),
          };
        }),

      remove: (id) =>
        set((state) => ({
          items: state.items.filter((i) => i.menu_item_id !== id),
        })),

      clear: () => set({ items: [] }),

      subtotal: () => get().items.reduce((acc, i) => acc + i.line_total_cop, 0),
      count: () => get().items.reduce((acc, i) => acc + i.quantity, 0),
    }),
    { name: "noah_cart_v1" }
  )
);
