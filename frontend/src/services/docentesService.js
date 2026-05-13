import apiClient from "./apiClient";

export async function getDocentesPage({ query = "", page = 1, pageSize = 8 } = {}) {
  const response = await apiClient.get("/docentes/", {
    params: {
      query,
      page,
      page_size: pageSize,
    },
  });

  return response.data;
}

export async function createDocente(payload) {
  const response = await apiClient.post("/docentes/", payload);
  return response.data;
}