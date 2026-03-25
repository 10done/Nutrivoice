/* global NUTRIVOICE_API */

async function apiFetch(path, options = {}) {
  const token = typeof getToken === "function" ? getToken() : null;
  const headers = { ...(options.headers || {}) };
  if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const base = typeof NUTRIVOICE_API !== "undefined" ? NUTRIVOICE_API : "/api";
  const r = await fetch(`${base}${path}`, { ...options, headers });
  if (r.status === 401) {
    if (typeof clearToken === "function") clearToken();
    if (!path.startsWith("/auth/")) window.location.href = "/login.html";
    throw new Error("Unauthorized");
  }
  return r;
}
