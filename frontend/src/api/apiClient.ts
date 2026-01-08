import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/";

export const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// alias para compatibilidad con imports antiguos
export const api = apiClient;
