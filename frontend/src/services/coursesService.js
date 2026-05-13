import apiClient from "./apiClient";

export async function getCoursesPage({ query = "", page = 1, pageSize = 6 } = {}) {
  const response = await apiClient.get("/courses/", {
    params: {
      query,
      page,
      page_size: pageSize,
    },
  });

  return response.data;
}

export async function createCourse(payload) {
  const response = await apiClient.post("/courses/", payload);
  return response.data;
}

export async function getCourseDetail({ asignacionId, periodoId, fecha }) {
  const response = await apiClient.get("/courses/detail/", {
    params: { asignacion_id: asignacionId, periodo_id: periodoId, fecha },
  });
  return response.data;
}

export async function updateGrades({ asignacionId, periodoId, notas }) {
  const response = await apiClient.post("/grades/update/", {
    asignacion_id: asignacionId,
    periodo_id: periodoId,
    notas,
  });
  return response.data;
}
