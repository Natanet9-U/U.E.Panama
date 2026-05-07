import apiClient from "./apiClient";

export async function getReportsPage({ periodoId = "" } = {}) {
  const response = await apiClient.get("/reports/", {
    params: {
      periodo_id: periodoId,
    },
  });

  return response.data;
}
