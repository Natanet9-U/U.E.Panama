import apiClient from "./apiClient";

export async function getSchedulesPage({ gradoId = "" } = {}) {
  const params = new URLSearchParams();
  if (gradoId) {
    params.append("grado_id", gradoId);
  }

  const queryString = params.toString();
  const url = queryString ? `/schedules/?${queryString}` : "/schedules/";

  return apiClient
    .get(url)
    .then((response) => response.data)
    .catch((error) => {
      if (error.response?.status === 401) {
        throw new Error("No autorizado");
      }
      throw error;
    });
}
