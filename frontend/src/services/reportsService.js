import apiClient from "./apiClient";

export async function getReportsPage({ periodoId = "", trimestre = "" } = {}) {
  const response = await apiClient.get("/reports/", {
    params: {
      periodo_id: periodoId,
      trimestre,
    },
  });

  return response.data;
}

export async function downloadReportsDocument({ periodoId = "", trimestre = "" } = {}) {
  const response = await apiClient.get("/reports/download/", {
    params: {
      periodo_id: periodoId,
      trimestre,
    },
    responseType: "blob",
  });

  return response;
}
