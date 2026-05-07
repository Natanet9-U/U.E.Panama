import apiClient from "./apiClient";

export async function getGradesPage({ query = "", periodoId = "", page = 1, pageSize = 10 } = {}) {
  const response = await apiClient.get("/grades/", {
    params: {
      query,
      periodo_id: periodoId,
      page,
      page_size: pageSize,
    },
  });

  return response.data;
}
