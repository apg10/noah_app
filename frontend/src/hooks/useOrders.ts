import { useMutation, useQuery } from "@tanstack/react-query";
import { createOrder, getOrderByNumber } from "../api/noahApi";
import type { CreateOrderPayload } from "../api/noahApi";

export function useCreateOrder() {
  return useMutation({
    mutationFn: (payload: CreateOrderPayload) => createOrder(payload),
  });
}

export function useOrderTracking(orderNumber: string) {
  return useQuery({
    queryKey: ["order", orderNumber],
    queryFn: () => getOrderByNumber(orderNumber),
    enabled: Boolean(orderNumber),
    refetchInterval: 12_000, // polling recomendado v1
  });
}
