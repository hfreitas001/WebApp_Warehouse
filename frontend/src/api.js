const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  const res = await fetch(BASE + path, { ...options, headers });
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
