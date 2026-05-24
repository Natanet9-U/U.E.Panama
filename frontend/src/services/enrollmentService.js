import apiClient from "./apiClient";

export async function searchExistingStudent(ci) {
  const response = await apiClient.get("/enrollment/search/", {
    params: { rude: ci, ci },
  });
  return response.data;
}

export async function searchTutorByCI(ci) {
  const response = await apiClient.get("/enrollment/search-tutor/", {
    params: { ci },
  });
  return response.data;
}

export async function enrollNewStudent(payload) {
  const response = await apiClient.post("/enrollment/new/", payload);
  return response.data;
}

export async function reEnrollStudent(ci, gradoId) {
  const response = await apiClient.post("/enrollment/re-enroll/", {
    rude: ci,
    ci,
    grado_id: gradoId,
  });
  return response.data;
}

export async function getEnrollmentCatalogs() {
  const response = await apiClient.get("/enrollment/catalogs/");
  return response.data;
}
