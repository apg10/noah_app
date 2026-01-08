// src/api/endpoints.ts
export const endpoints = {
  restaurants: () => `restaurants/`,
  categories: () => `categories/`,
  menuItems: () => `menu-items/`,
  featuredItems: () => `menu-items/featured/`, // opcional si lo expones así
  orders: () => `orders/`,
  orderByNumber: (orderNumber: string) => `orders/${orderNumber}/`, // tracking público
  couponsValidate: () => `coupons/validate/`, // opcional
  salesSummary: () => `sales-summary/`, // admin
};
