import apiClient from "./apiClient";

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

export async function loginRequest(email, password) {
  const response = await apiClient.post("/auth/login/", { email, password });
  const { token, usuario } = response.data;

  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(usuario));

  return usuario;
}

export async function getCurrentUser() {
  const response = await apiClient.get("/auth/me/");
  return response.data.usuario;
}

export function getStoredUser() {
  const rawUser = localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser);
  } catch (_err) {
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
