const TOKEN_KEY = "nv_token";

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(t) {
  sessionStorage.setItem(TOKEN_KEY, t);
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/login.html";
  }
}

function logout() {
  clearToken();
  window.location.href = "/login.html";
}
