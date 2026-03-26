/* global NUTRIVOICE_API */

async function apiFetch(path, options = {}) {
  const token = typeof getToken === "function" ? getToken() : null;
  const headers = { ...(options.headers || {}) };
  if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const publicAuth = path === "/auth/login" || path === "/auth/register";
  if (token && !publicAuth) headers["Authorization"] = `Bearer ${token}`;
  const base = typeof NUTRIVOICE_API !== "undefined" ? NUTRIVOICE_API : "/api";
  let r;
  try {
    r = await fetch(`${base}${path}`, { ...options, headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(msg || "Could not reach the server");
  }
  if (r.status === 401) {
    // Let login/register read JSON body (e.g. "Invalid credentials"); don't mislabel as network error.
    if (path !== "/auth/login" && path !== "/auth/register") {
      if (typeof clearToken === "function") clearToken();
      window.location.href = "/login.html";
      throw new Error("Unauthorized");
    }
  }
  return r;
}
