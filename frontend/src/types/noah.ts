export type OrderStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "READY"
  | "COMPLETED"
  | "CANCELLED";

export type MenuCategory = {
  id: number;
  name: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
};

export type MenuItem = {
  id: number;
  restaurant: number;
  category: number | null;
  name: string;
  description?: string;
  price_cop: number;
  cost_cop?: number;
  stock?: number;
  image_url?: string;
  is_active?: boolean;
  is_combination?: boolean;
  average_prep_minutes?: number;
};

export type CartItem = {
  menu_item_id: number;
  name: string;
  unit_price_cop: number;
  quantity: number;
  line_total_cop: number;
};

export type OrderItemPayload = {
  menu_item: number; // <-- backend
  quantity: number;
  notes?: string;
};

export type CreateOrderPayload = {
  restaurant: number;
  channel: "web" | "whatsapp" | "phone" | "walkin";
  customer: { name: string; phone: string; email?: string };
  delivery_address: {
    address_line: string;
    neighborhood: string;
    city?: string;
    notes?: string;
  };
  coupon_code?: string;
  customer_notes?: string;
  items: OrderItemPayload[];
};

export type Order = {
  id: number;
  order_number: string;
  restaurant: number;
  status: OrderStatus;
  subtotal_cop: number;
  discount_cop: number;
  delivery_fee_cop: number;
  total_cop: number;
  customer_notes?: string;
  created_at?: string;

  pending_at?: string | null;
  in_progress_at?: string | null;
  ready_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;

  items?: {
    id: number;
    menu_item: number;
    quantity: number;
    unit_price_cop: number;
    line_total_cop: number;
    notes?: string;
  }[];
};
