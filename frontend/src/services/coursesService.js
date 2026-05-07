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
