import apiClient from "./apiClient";

export async function getStudentsPage({ query = "", gradoId = "", page = 1, pageSize = 8 } = {}) {
  const response = await apiClient.get("/students/", {
    params: {
      query,
      grado_id: gradoId,
      page,
      page_size: pageSize,
    },
  });

  return response.data;
}

export async function createStudent(payload) {
  const response = await apiClient.post("/students/", payload);
  return response.data;
}

