/* global apiFetch, setToken */

function formatDetail(detail) {
  if (detail == null) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e.msg || JSON.stringify(e)).join("; ");
  return String(detail);
}

document.addEventListener("DOMContentLoaded", () => {
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const msg = document.getElementById("auth-msg");

  if (typeof getToken === "function" && getToken()) {
    window.location.href = "/index.html";
    return;
  }

  function showForms(which) {
    if (which === "login") {
      formLogin?.classList.remove("hidden");
      formRegister?.classList.add("hidden");
    } else {
      formLogin?.classList.add("hidden");
      formRegister?.classList.remove("hidden");
    }
  }

  tabLogin?.addEventListener("click", () => showForms("login"));
  tabRegister?.addEventListener("click", () => showForms("register"));

  formLogin?.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.textContent = "";
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    try {
      const r = await apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      const data = await r.json();
      if (!r.ok) {
        msg.textContent = formatDetail(data.detail) || "Login failed";
        return;
      }
      setToken(data.access_token);
      window.location.href = "/index.html";
    } catch (err) {
      msg.textContent = "Network error";
    }
  });

  formRegister?.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.textContent = "";
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;
    try {
      const r = await apiFetch("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
      const data = await r.json();
      if (!r.ok) {
        msg.textContent = formatDetail(data.detail) || "Register failed";
        return;
      }
      setToken(data.access_token);
      window.location.href = "/index.html";
    } catch (err) {
      msg.textContent = "Network error";
    }
  });
});
