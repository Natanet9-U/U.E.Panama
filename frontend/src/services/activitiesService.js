import apiClient from "./apiClient";

const activitiesService = {
  getActividades: async ({ asignacionId }) => {
    const response = await apiClient.get("/actividades/", {
      params: { asignacion_id: asignacionId },
    });
    return response.data;
  },

  createActividad: async ({ asignacionId, nombre, puntaje_maximo, dimensionId, fecha }) => {
    const response = await apiClient.post("/actividades/", {
      asignacion_id: asignacionId,
      nombre,
      puntaje_maximo,
      dimension_id: dimensionId,
      fecha,
    });
    return response.data;
  },

  deleteActividad: async ({ actividadId }) => {
    const response = await apiClient.delete(`/actividades/${actividadId}/`);
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

  recomputeTrimestre: async ({ asignacionId, periodoId }) => {
    const response = await apiClient.post("/grades/recompute-actividades/", {
      asignacion_id: asignacionId,
      periodo_id: periodoId,
    });
    return response.data;
  },
};

export default activitiesService;
