import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  timeout: 10000,
});

export async function getOperadoras(page = 1, limit = 10) {
  const { data } = await api.get("/api/operadoras", { params: { page, limit } });
  return data;
}

export async function getOperadoraByCnpj(cnpj) {
  const { data } = await api.get(`/api/operadoras/${encodeURIComponent(cnpj)}`);
  return data;
}

export async function getDespesasOperadora(cnpj) {
  const { data } = await api.get(`/api/operadoras/${encodeURIComponent(cnpj)}/despesas`);
  return data;
}

export async function getEstatisticas() {
  const { data } = await api.get("/api/estatisticas");
  return data;
}

export function formatCnpj(cnpj) {
  if (!cnpj) return "";
  const s = String(cnpj).replace(/\D/g, "").slice(0, 14);
  if (s.length !== 14) return s;
  return s.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}
