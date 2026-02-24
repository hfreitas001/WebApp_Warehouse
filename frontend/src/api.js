// Em produção (Vercel) defina VITE_API_URL no painel. Fallback: localhost em dev, Render em produção.
const _envApi = (import.meta.env.VITE_API_URL || "").trim().replace(/\/+$/, "");
const _isLocal = typeof window !== "undefined" && /^(localhost|127\.0\.0\.1)$/.test(window.location?.hostname || "");
const BASE = _envApi || (_isLocal ? "http://localhost:8000" : "https://webapp-warehouse.onrender.com");
const API_TIMEOUT_MS = 65000;

function getToken() {
  return localStorage.getItem("wms_token");
}

export async function api(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: "Bearer " + token }),
    ...options.headers,
  };
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout ?? API_TIMEOUT_MS);
  let res;
  try {
    const url = (BASE.replace(/\/+$/, "") + path).replace(/([^:]\/)\/+/g, "$1");
    res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error("A API demorou para responder. Tente novamente (a API pode estar acordando).");
    }
    const isNetwork = !err.message || err.message === "Failed to fetch" || err.message.includes("NetworkError");
    if (isNetwork) {
      const tip = BASE.includes("localhost")
        ? " Confira se o backend está rodando (ex.: python -m uvicorn api.main:app --reload --port 8000)."
        : " Verifique se a API no Render está no ar (abra o /health no navegador).";
      throw new Error("Não foi possível conectar à API." + tip);
    }
    throw new Error(err.message || "Falha na conexão. Tente novamente.");
  }
  clearTimeout(timeoutId);
  if (res.status === 401) {
    localStorage.removeItem("wms_token");
    localStorage.removeItem("wms_user");
    window.dispatchEvent(new Event("storage"));
    throw new Error("Nao autorizado");
  }
  const data = res.ok ? await res.json().catch(() => ({})) : null;
  if (!res.ok) throw new Error(data && data.detail ? data.detail : res.statusText);
  return data;
}

export const auth = {
  login: (email, password) => api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => api("/auth/me"),
};
export const data = {
  load: () => api("/data/load"),
  stock: () => api("/data/stock"),
  storages: () => api("/data/storages"),
  depositoEntrada: (body) =>
    api("/data/deposito/entrada", { method: "POST", body: JSON.stringify(body) }),
  depositoSaida: (body) =>
    api("/data/deposito/saida", { method: "POST", body: JSON.stringify(body) }),
  inboundBatch: (body) =>
    api("/data/inbound/batch", { method: "POST", body: JSON.stringify(body) }),
  outboundConfirm: (body) =>
    api("/data/outbound/confirm", { method: "POST", body: JSON.stringify(body) }),
};
export const movements = {
  list: () => api("/movements"),
  log: (body) => api("/movements", { method: "POST", body: JSON.stringify(body) }),
};
export const orders = {
  open: () => api("/orders/open"),
  fulfilled: () => api("/orders/fulfilled"),
};
export const admin = {
  pending: () => api("/admin/users/pending"),
  users: () => api("/admin/users"),
  approve: (email) => api("/admin/users/approve", { method: "POST", body: JSON.stringify({ email }) }),
  updateModules: (email, allowed_modules) =>
    api("/admin/users/modules", { method: "PUT", body: JSON.stringify({ email, allowed_modules }) }),
};
