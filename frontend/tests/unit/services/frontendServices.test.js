import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/services/apiClient", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import apiClient from "../../../src/services/apiClient";
import { getStudentsPage, createStudent } from "../../../src/services/studentsService";
import { getCoursesPage, createCourse, getCourseDetail, updateGrades } from "../../../src/services/coursesService";
import { getDocentesPage, createDocente } from "../../../src/services/docentesService";
import { markAttendance, getAttendance, createLicencia } from "../../../src/services/attendanceService";
import { getGradesPage } from "../../../src/services/gradesService";
import { searchExistingStudent, enrollNewStudent, reEnrollStudent, getEnrollmentCatalogs } from "../../../src/services/enrollmentService";
import { getReportsPage } from "../../../src/services/reportsService";
import { getSchedulesPage } from "../../../src/services/schedulesService";
import activitiesService from "../../../src/services/activitiesService";

describe("frontend services", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("studentsService usa los parametros correctos", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });
    apiClient.post.mockResolvedValue({ data: { created: true } });

    await getStudentsPage({ query: "ana", gradoId: "g-1", page: 2, pageSize: 5 });
    await createStudent({ nombres: "Ana" });

    expect(apiClient.get).toHaveBeenCalledWith("/students/", {
      params: { query: "ana", grado_id: "g-1", page: 2, page_size: 5 },
    });
    expect(apiClient.post).toHaveBeenCalledWith("/students/", { nombres: "Ana" });
  });

  it("coursesService consulta y actualiza cursos", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });
    apiClient.post.mockResolvedValue({ data: { ok: true } });

    await getCoursesPage({ query: "mat", page: 3, pageSize: 7 });
    await createCourse({ area_name: "Matematicas" });
    await getCourseDetail({ asignacionId: "a-1", periodoId: "p-1", fecha: "2026-05-22" });
    await updateGrades({ asignacionId: "a-1", periodoId: "p-1", notas: [] });

    expect(apiClient.get).toHaveBeenCalledWith("/courses/", {
      params: { query: "mat", page: 3, page_size: 7 },
    });
    expect(apiClient.get).toHaveBeenCalledWith("/courses/detail/", {
      params: { asignacion_id: "a-1", periodo_id: "p-1", fecha: "2026-05-22" },
    });
    expect(apiClient.post).toHaveBeenCalledWith("/courses/", { area_name: "Matematicas" });
    expect(apiClient.post).toHaveBeenCalledWith("/grades/update/", {
      asignacion_id: "a-1",
      periodo_id: "p-1",
      notas: [],
    });
  });

  it("docentesService y attendanceService envian payloads correctos", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });
    apiClient.post.mockResolvedValue({ data: { ok: true } });

    await getDocentesPage({ query: "ana", page: 1, pageSize: 4 });
    await createDocente({ nombres: "Ana", apellido: "Perez" });
    await markAttendance({ asignacionId: "a-1", fecha: "2026-05-22", estados: { s1: "Presente" } });
    await getAttendance({ asignacionId: "a-1", fecha: "2026-05-22" });
    await createLicencia({ estudiante_id: "e-1" });

    expect(apiClient.get).toHaveBeenCalledWith("/docentes/", {
      params: { query: "ana", page: 1, page_size: 4 },
    });
    expect(apiClient.post).toHaveBeenCalledWith("/docentes/", { nombres: "Ana", apellido: "Perez" });
    expect(apiClient.post).toHaveBeenCalledWith("/attendance/", {
      asignacion_id: "a-1",
      fecha: "2026-05-22",
      estados: { s1: "Presente" },
    });
    expect(apiClient.get).toHaveBeenCalledWith("/attendance/", {
      params: { asignacion_id: "a-1", fecha: "2026-05-22" },
    });
    expect(apiClient.post).toHaveBeenCalledWith("/licencias/", { estudiante_id: "e-1" });
  });

  it("grades, enrollment, reports y schedules usan endpoints esperados", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });
    apiClient.post.mockResolvedValue({ data: { ok: true } });

    await getGradesPage({ query: "ana", periodoId: "p-1", page: 1, pageSize: 10 });
    await searchExistingStudent("ci-1");
    await enrollNewStudent({ nombres: "Ana" });
    await reEnrollStudent("ci-1", "g-1");
    await getEnrollmentCatalogs();
    await getReportsPage({ periodoId: "p-1" });
    await getSchedulesPage({ gradoId: "g-1" });

    expect(apiClient.get).toHaveBeenCalledWith("/grades/", {
      params: { query: "ana", periodo_id: "p-1", page: 1, page_size: 10 },
    });
    expect(apiClient.get).toHaveBeenCalledWith("/enrollment/search/", { params: { rude: "ci-1", ci: "ci-1" } });
    expect(apiClient.post).toHaveBeenCalledWith("/enrollment/new/", { nombres: "Ana" });
    expect(apiClient.post).toHaveBeenCalledWith("/enrollment/re-enroll/", { rude: "ci-1", ci: "ci-1", grado_id: "g-1" });
    expect(apiClient.get).toHaveBeenCalledWith("/enrollment/catalogs/");
    expect(apiClient.get).toHaveBeenCalledWith("/reports/", { params: { periodo_id: "p-1", trimestre: "" } });
    expect(apiClient.get).toHaveBeenCalledWith("/schedules/?grado_id=g-1");
  });

  it("activitiesService usa los endpoints de actividades", async () => {
    apiClient.get.mockResolvedValue({ data: { ok: true } });
    apiClient.post.mockResolvedValue({ data: { ok: true } });

    await activitiesService.getActividades({ asignacionId: "a-1" });
    await activitiesService.createActividad({ asignacionId: "a-1", nombre: "Tarea", puntaje_maximo: 100 });
    await activitiesService.updateActividadesNotas({ asignacionId: "a-1", actividadId: "act-1", notas: [] });
    await activitiesService.getActividadesNotas({ asignacionId: "a-1" });

    expect(apiClient.get).toHaveBeenCalledWith("/actividades/", { params: { asignacion_id: "a-1" } });
    expect(apiClient.post).toHaveBeenCalledWith("/actividades/", {
      asignacion_id: "a-1",
      nombre: "Tarea",
      puntaje_maximo: 100,
    });
    expect(apiClient.post).toHaveBeenCalledWith("/actividades/notas/", {
      asignacion_id: "a-1",
      actividad_id: "act-1",
      notas: [],
    });
    expect(apiClient.get).toHaveBeenCalledWith("/actividades/notas-estudiante/", { params: { asignacion_id: "a-1" } });
  });

  it("schedulesService normaliza errores 401", async () => {
    apiClient.get.mockRejectedValue({ response: { status: 401 } });

    await expect(getSchedulesPage({ gradoId: "g-1" })).rejects.toThrow("No autorizado");
  });
});