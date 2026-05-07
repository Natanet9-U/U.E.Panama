import apiClient from "./apiClient";

export async function getDashboardData() {
  const response = await apiClient.get("/dashboard/");
  return response.data;
}
