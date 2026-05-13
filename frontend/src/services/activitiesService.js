import apiClient from "./apiClient";

const activitiesService = {
  getActividades: async ({ asignacionId }) => {
    const response = await apiClient.get("/actividades/", {
      params: { asignacion_id: asignacionId },
    });
    return response.data;
  },

  createActividad: async ({ asignacionId, nombre, puntaje_maximo }) => {
    const response = await apiClient.post("/actividades/", {
      asignacion_id: asignacionId,
      nombre,
      puntaje_maximo,
    });
    return response.data;
  },

  updateActividadesNotas: async ({ asignacionId, actividadId, notas }) => {
    const response = await apiClient.post("/actividades/notas/", {
      asignacion_id: asignacionId,
      actividad_id: actividadId,
      notas,
    });
    return response.data;
  },

  getActividadesNotas: async ({ asignacionId }) => {
    const response = await apiClient.get("/actividades/notas-estudiante/", {
      params: { asignacion_id: asignacionId },
    });
    return response.data;
  },
};

export default activitiesService;
