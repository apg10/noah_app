import { useQuery } from "@tanstack/react-query";
import { getCategories, getMenuItems } from "../api/noahApi";

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(),
  });
}

export function useMenuItems() {
  return useQuery({
    queryKey: ["menu-items"],
    queryFn: () => getMenuItems(),
  });
}
