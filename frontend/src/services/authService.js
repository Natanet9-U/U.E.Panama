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

export async function changePasswordRequest(currentPassword, newPassword) {
  const response = await apiClient.post("/auth/change-password/", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return response.data;
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
  //Poner false para requerir login
  const DEVELOPMENT_MODE = true;
  if (DEVELOPMENT_MODE) return true;
  
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function logoutRequest() {
  try {
    await apiClient.post("/auth/logout/");
  } catch (_err) {
    // ignore server errors and continue cleaning client state
  }
  logout();
}
