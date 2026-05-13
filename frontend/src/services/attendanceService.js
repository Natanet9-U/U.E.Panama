import apiClient from "./apiClient";

export async function markAttendance({ asignacionId, fecha, estados }) {
  const payload = {
    asignacion_id: asignacionId,
    fecha,
    estados,
  };
  const response = await apiClient.post("/attendance/", payload);
  return response.data;
}

export async function getAttendance({ asignacionId, fecha }) {
  const response = await apiClient.get("/attendance/", {
    params: { asignacion_id: asignacionId, fecha },
  });
  return response.data;
}

export async function createLicencia(payload) {
  const response = await apiClient.post("/licencias/", payload);
  return response.data;
}
