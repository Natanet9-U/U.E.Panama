import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getCourseDetail, updateGrades } from "../../services/coursesService";
import { getAttendance, markAttendance } from "../../services/attendanceService";
import activitiesService from "../../services/activitiesService";

const EMPTY_ARRAY = [];
const EMPTY_OBJECT = {};

function normalizeText(value) {
  return (value || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function isAutoevaluacionDimension(dimension) {
  return normalizeText(dimension?.nombre).startsWith("autoevalu");
}



function CourseDetailPage() {
  const [search] = useSearchParams();
  const asignacionId = search.get("asignacion_id");
  const [periodoId, setPeriodoId] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [data, setData] = useState(null);
  const [attendance, setAttendance] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingAll, setSavingAll] = useState(false);
  const [tab, setTab] = useState("attendance");
  const [actividadesNotas, setActividadesNotas] = useState({});
  const [autoevaluacion, setAutoevaluacion] = useState({});
  const [nuevoActividad, setNuevoActividad] = useState({ nombre: "", puntaje_maximo: 100, dimensionId: "", fecha: new Date().toISOString().slice(0, 10) });
  const [error, setError] = useState("");
  const [hoveredActividad, setHoveredActividad] = useState(null);
  const [collapsedDims, setCollapsedDims] = useState({});
  const [tableZoom, setTableZoom] = useState(100);

  const estudiantes = data?.estudiantes || EMPTY_ARRAY;
  const periodos = data?.periodos || EMPTY_ARRAY;
  const dimensiones = data?.dimensiones || EMPTY_ARRAY;
  const actividades = data?.actividades || EMPTY_ARRAY;
  const notas = data?.notas || EMPTY_ARRAY;
  const activityNotes = useMemo(() => data?.actividad_notas || EMPTY_OBJECT, [data]);

  const dimensionNotes = useMemo(() => {
    const map = {};
    notas.forEach((nota) => {
      map[nota.estudiante_id] = { total: nota.total, detalles: {} };
      (nota.detalles || []).forEach((detalle) => {
        map[nota.estudiante_id].detalles[detalle.dimension_id] = detalle.valor;
      });
    });
    return map;
  }, [notas]);

  const autoDimension = useMemo(() => dimensiones.find((dimension) => isAutoevaluacionDimension(dimension)), [dimensiones]);
  const dimensionGroups = useMemo(() => dimensiones.filter((dimension) => !isAutoevaluacionDimension(dimension)), [dimensiones]);

  const activitiesByDimension = useMemo(() => {
    const groups = {};
    dimensionGroups.forEach((dimension) => {
      groups[dimension.id] = actividades.filter((activity) => String(activity.dimension_id) === String(dimension.id));
    });
    return groups;
  }, [actividades, dimensionGroups]);

  const selectedPeriodLabel = useMemo(() => {
    const selected = periodos.find((periodo) => periodo.id === periodoId);
    return selected ? selected.nombre : "Trimestre pendiente";
  }, [periodoId, periodos]);

  useEffect(() => {
    if (!asignacionId) return;
    let mounted = true;
    setLoading(true);
    getCourseDetail({ asignacionId, periodoId })
      .then((response) => {
        if (!mounted) return;
        setData(response);
        setError("");
        if (!periodoId) {
          const activePeriod = (response.periodos || []).find((periodo) => periodo.activo) || (response.periodos || [])[0];
          if (activePeriod) setPeriodoId(activePeriod.id);
        }
      })
      .catch((requestError) => {
        if (!mounted) return;
        setError(requestError?.response?.data?.error || "No fue posible cargar el curso");
        setData(null);
      })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [asignacionId, periodoId]);

  useEffect(() => {
    if (!asignacionId) return;
    getAttendance({ asignacionId, fecha })
      .then((resp) => {
        const map = {};
        (resp.asistencias || []).forEach((asistencia) => {
          map[asistencia.estudiante_id] = asistencia.estado;
        });
        setAttendance(map);
      })
      .catch(() => setAttendance({}));
  }, [asignacionId, fecha]);

  useEffect(() => {
    if (!asignacionId) return;
    const nextNotas = {};
    Object.entries(activityNotes || {}).forEach(([actividadId, valores]) => {
      nextNotas[actividadId] = { ...valores };
    });
    setActividadesNotas(nextNotas);
    const nextAuto = {};
    estudiantes.forEach((estudiante) => {
      nextAuto[estudiante.id] = Number(dimensionNotes[estudiante.id]?.detalles?.[autoDimension?.id] ?? 0);
    });
    setAutoevaluacion(nextAuto);
  }, [asignacionId, activityNotes, autoDimension?.id, dimensionNotes, estudiantes]);

  useEffect(() => {
    if (!dimensionGroups.length) return;
    setNuevoActividad((current) => {
      if (current.dimensionId) return current;
      return { ...current, dimensionId: dimensionGroups[0].id };
    });
  }, [dimensionGroups]);

  const refreshCourse = async () => {
    const response = await getCourseDetail({ asignacionId, periodoId });
    setData(response);
    return response;
  };

  const toggleAttendance = (estudianteId) => {
    setAttendance((current) => ({ ...current, [estudianteId]: current[estudianteId] === "present" ? "absent" : "present" }));
  };

  const submitAttendance = async () => {
    setSaving(true);
    const estados = {};
    Object.entries(attendance).forEach(([key, value]) => { estados[key] = value || "absent"; });
    try {
      await markAttendance({ asignacionId, fecha, estados });
      alert("Asistencias guardadas");
    } catch (requestError) {
      alert(requestError?.response?.data?.error || "Error al guardar asistencia");
    } finally { setSaving(false); }
  };

  const handleActivityValueChange = (actividadId, estudianteId, value) => {
    setActividadesNotas((current) => ({
      ...current,
      [actividadId]: {
        ...(current[actividadId] || {}),
        [estudianteId]: value === "" ? "" : Math.max(0, Number(value)),
      },
    }));
  };

  const handleAutoevaluacionChange = (estudianteId, value) => {
    setAutoevaluacion((current) => ({
      ...current,
      [estudianteId]: value === "" ? "" : Math.max(0, Number(value)),
    }));
  };

  const getSavedDimensionValue = (estudianteId, dimensionId) => Number(dimensionNotes[estudianteId]?.detalles?.[dimensionId] ?? 0);

  const getActivityValue = (actividadId, estudianteId) => {
    const currentValue = actividadesNotas[actividadId]?.[estudianteId];
    if (currentValue === undefined) return activityNotes[actividadId]?.[estudianteId] ?? "";
    return currentValue;
  };

  const getDimensionHeaderSpan = (dimension) => {
    const groupedActivities = activitiesByDimension[dimension.id] || [];
    return groupedActivities.length + 1;
  };

  const getFinalScore = (estudianteId) => {
    return dimensiones.reduce((total, dimension) => total + getDimensionScore(dimension, estudianteId), 0);
  };

  const getDimensionScore = (dimension, estudianteId) => {
    if (!dimension) return 0;
    if (autoDimension && dimension.id === autoDimension.id) {
      const draftValue = autoevaluacion[estudianteId];
      if (draftValue === "") return getSavedDimensionValue(estudianteId, dimension.id);
      return Math.max(0, Math.min(Number(draftValue || 0), Number(dimension.puntaje_maximo || 0)));
    }
    const dimensionActivities = activitiesByDimension[dimension.id] || [];
    if (!dimensionActivities.length) return getSavedDimensionValue(estudianteId, dimension.id);
    const ratios = dimensionActivities
      .map((actividad) => {
        const value = getActivityValue(actividad.id, estudianteId);
        if (value === "" || value === null || value === undefined) return null;
        const max = Number(actividad.puntaje_maximo || 0);
        if (!max) return null;
        return Number(value) / max;
      })
      .filter((value) => value !== null);
    if (!ratios.length) return getSavedDimensionValue(estudianteId, dimension.id);
    const averageRatio = ratios.reduce((sum, value) => sum + value, 0) / ratios.length;
    const rawValue = Math.round(averageRatio * Number(dimension.puntaje_maximo || 0));
    return Math.max(0, Math.min(rawValue, Number(dimension.puntaje_maximo || 0)));
  };

  const agregarActividad = async () => {
    if (!nuevoActividad.nombre.trim()) { alert("Ingresa el nombre de la actividad"); return; }
    if (!nuevoActividad.dimensionId) { alert("Selecciona una dimensión"); return; }
    setSaving(true);
    try {
      await activitiesService.createActividad({
        asignacionId,
        nombre: nuevoActividad.nombre.trim(),
        puntaje_maximo: Number(nuevoActividad.puntaje_maximo || 100),
        dimensionId: nuevoActividad.dimensionId,
        fecha: nuevoActividad.fecha || fecha,
      });
      setNuevoActividad((current) => ({ ...current, nombre: "", puntaje_maximo: 100 }));
      await refreshCourse();
      alert("Actividad creada");
    } catch (requestError) {
      alert(requestError?.response?.data?.error || "Error al crear actividad");
    } finally { setSaving(false); }
  };

  const eliminarActividad = async (actividadId) => {
    if (!window.confirm("¿Eliminar esta actividad?")) return;
    setSaving(true);
    try {
      await activitiesService.deleteActividad({ actividadId });
      await refreshCourse();
      alert("Actividad eliminada");
    } catch (requestError) {
      alert(requestError?.response?.data?.error || "Error al eliminar actividad");
    } finally { setSaving(false); }
  };

  const guardarCalificaciones = async () => {
    setSavingAll(true);
    try {
      await Promise.all(
        actividades.map((actividad) => activitiesService.updateActividadesNotas({ asignacionId, actividadId: actividad.id, notas: actividadesNotas[actividad.id] || {} })),
      );
      if (autoDimension) {
        const payload = estudiantes.map((estudiante) => ({
          estudiante_id: estudiante.id,
          detalles: [{ dimension_id: autoDimension.id, valor: Math.max(0, Math.min(Number(autoevaluacion[estudiante.id] ?? getSavedDimensionValue(estudiante.id, autoDimension.id) ?? 0), Number(autoDimension.puntaje_maximo || 0))), }],
        }));
        await updateGrades({ asignacionId, periodoId, notas: payload });
      }
      await activitiesService.recomputeTrimestre({ asignacionId, periodoId });
      await refreshCourse();
      alert("Calificaciones guardadas");
    } catch (requestError) {
      alert(requestError?.response?.data?.error || "Error al guardar calificaciones");
    } finally { setSavingAll(false); }
  };

  if (!asignacionId) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm font-medium text-slate-600">Asignación no especificada</div>;
  if (loading) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm font-medium text-slate-600">Cargando...</div>;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.06),rgba(255,255,255,0.98),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">Detalle del curso</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Calificaciones del trimestre</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Tabla por dimensión, actividades editables, autoevaluación fija y final sobre 100 puntos.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700">{selectedPeriodLabel}</div>
        </div>
        {periodos.length ? (
          <div className="mt-6 flex flex-wrap gap-2">
            {periodos.map((periodo) => (
              <button key={periodo.id} type="button" onClick={() => setPeriodoId(periodo.id)} className={`rounded-full border px-4 py-2 text-sm font-semibold transition ${periodo.id === periodoId ? "border-blue-200 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-950"}`}>
                {periodo.nombre}
              </button>
            ))}
          </div>
        ) : null}
      </header>

      {error ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div> : null}

      <div className="border-b border-slate-200">
        <div className="flex gap-4">
          <button type="button" onClick={() => setTab("attendance")} className={`px-4 py-2 ${tab === "attendance" ? "border-b-2 border-blue-600 font-bold text-blue-700" : "text-slate-600"}`}>Asistencia</button>
          <button type="button" onClick={() => setTab("grades")} className={`px-4 py-2 ${tab === "grades" ? "border-b-2 border-blue-600 font-bold text-blue-700" : "text-slate-600"}`}>Notas</button>
        </div>
      </div>

      {tab === "attendance" ? (
        <div className="space-y-4 rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Fecha</label>
              <input type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-300" />
            </div>
            <div className="ml-auto">
              <button type="button" onClick={submitAttendance} disabled={saving} className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">Guardar asistencia</button>
            </div>
          </div>
          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                  <th className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {estudiantes.map((estudiante) => (
                  <tr key={estudiante.id} className="hover:bg-slate-50/80">
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">{estudiante.nombre.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{estudiante.nombre}</p>
                          <p className="text-xs text-slate-500">{estudiante.id.slice(0, 8)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <button type="button" onClick={() => toggleAttendance(estudiante.id)} className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold ${attendance[estudiante.id] === "present" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
                        {attendance[estudiante.id] === "present" ? "Presente" : "Ausente"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "grades" ? (
        <div className="space-y-6">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-xl font-black text-slate-950">Nueva actividad</h2>
                <p className="mt-1 text-sm text-slate-500">Selecciona una dimensión. La autoevaluación se mantiene como columna fija.</p>
              </div>
              <div className="flex gap-3 items-center">
                <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1">
                  <button onClick={() => setTableZoom(Math.max(80, tableZoom - 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Reducir zoom">−</button>
                  <span className="w-10 text-center text-xs font-bold text-slate-600">{tableZoom}%</span>
                  <button onClick={() => setTableZoom(Math.min(140, tableZoom + 10))} className="rounded px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white transition" title="Aumentar zoom">+</button>
                </div>
                <button type="button" onClick={guardarCalificaciones} disabled={savingAll} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50">Guardar trimestre</button>
              </div>
            </div>
            <div className="mt-6 grid gap-4 xl:grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_auto]">
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Actividad</label>
                <input value={nuevoActividad.nombre} onChange={(event) => setNuevoActividad((current) => ({ ...current, nombre: event.target.value }))} placeholder="Ej: Práctica 1, Exposición, Proyecto..." className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Dimensión</label>
                <select value={nuevoActividad.dimensionId} onChange={(event) => setNuevoActividad((current) => ({ ...current, dimensionId: event.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white">
                  {dimensionGroups.map((dimension) => (<option key={dimension.id} value={dimension.id}>{dimension.nombre}</option>))}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Puntaje máximo</label>
                <input type="number" min="1" value={nuevoActividad.puntaje_maximo} onChange={(event) => setNuevoActividad((current) => ({ ...current, puntaje_maximo: Number(event.target.value || 100) }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Fecha</label>
                <input type="date" value={nuevoActividad.fecha} onChange={(event) => setNuevoActividad((current) => ({ ...current, fecha: event.target.value }))} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-300 focus:bg-white" />
              </div>
              <div className="flex items-end">
                <button type="button" onClick={agregarActividad} disabled={saving} className="w-full rounded-2xl border border-blue-200 bg-blue-50 px-5 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50">Agregar</button>
              </div>
            </div>
          </section>

          <section className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '60vh', zoom: `${tableZoom}%` }}>
              <table className="min-w-max border-separate border-spacing-0">
                <thead>
                  <tr>
                    <th rowSpan={2} className="sticky left-0 top-0 z-20 border-b border-r border-slate-200 bg-slate-950 px-5 py-4 text-left text-[11px] font-bold uppercase tracking-wide text-white">Estudiante</th>
                    {dimensiones.map((dimension, dimIndex) => {
                      if (autoDimension && dimension.id === autoDimension.id) {
                        return (
                          <th key={dimension.id} rowSpan={2} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center text-[10px] font-semibold text-slate-700">
                            <div className="flex items-center justify-center gap-2">
                              <span className="font-bold">{dimension.nombre}</span>
                              <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold text-slate-500">{dimension.puntaje_maximo}</span>
                              <button type="button" title="Autoevaluación: siempre incluida (5 pts)" className="ml-2 text-slate-400 hover:text-slate-600">ℹ️</button>
                            </div>
                          </th>
                        );
                      }
                      const collapsed = !!collapsedDims[dimension.id];
                      const span = collapsed ? 1 : getDimensionHeaderSpan(dimension);
                      return (
                        <th key={dimension.id} colSpan={span} className={`border-b border-r border-slate-200 bg-slate-100 px-3 py-3 text-center text-[11px] font-bold uppercase tracking-wide text-slate-700 ${dimIndex > 0 ? "border-l-4 border-slate-200" : ""}`}>
                          <div className="flex items-center justify-center gap-2">
                            <span>{dimension.nombre}</span>
                            <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold text-slate-500">{dimension.puntaje_maximo}</span>
                            <button type="button" onClick={() => setCollapsedDims((c) => ({ ...c, [dimension.id]: !c[dimension.id] }))} className="ml-2 rounded-full border bg-white px-2 py-1 text-[11px] font-semibold text-slate-600" title={collapsed ? "Expandir" : "Colapsar"}>
                              {collapsed ? "▾" : "▴"}
                            </button>
                          </div>
                        </th>
                      );
                    })}
                    <th rowSpan={2} className="border-b border-slate-200 bg-slate-950 px-5 py-4 text-center text-[11px] font-bold uppercase tracking-wide text-white">Final</th>
                  </tr>
                  <tr>
                    {dimensiones.map((dimension) => {
                      if (autoDimension && dimension.id === autoDimension.id) return null;
                      const groupedActivities = activitiesByDimension[dimension.id] || [];
                      const collapsed = !!collapsedDims[dimension.id];
                      if (collapsed) return (<th key={`collapsed-${dimension.id}`} className="border-b border-r border-slate-200 bg-white px-3 py-3 text-center text-[10px] font-semibold text-slate-500">Nota</th>);
                      const actividadHeaders = groupedActivities.map((actividad, actIndex) => (
                        <th key={actividad.id} onMouseEnter={() => setHoveredActividad(actividad.id)} onMouseLeave={() => setHoveredActividad(null)} className={`border-b border-r border-slate-200 bg-white px-3 py-3 text-center text-[10px] font-bold uppercase tracking-wide text-slate-500 ${actIndex === 0 ? "border-l-4 border-slate-200 pl-3" : ""} ${hoveredActividad === actividad.id ? "ring-2 ring-blue-100" : ""}`} title={`${actividad.nombre} — ${dimension.nombre}`}>
                          <div className="flex items-center justify-between gap-1">
                            <div className="flex flex-col items-start">
                              <span className="truncate max-w-[140px] text-[10px] font-semibold text-slate-700">{actividad.nombre}</span>
                              <span className="text-[9px] text-slate-400">{actividad.puntaje_maximo}pts · {actividad.fecha}</span>
                            </div>
                            <button type="button" onClick={() => eliminarActividad(actividad.id)} className="ml-1 rounded-full border border-rose-200 bg-rose-50 px-2 py-1 text-[9px] font-bold text-rose-600 transition hover:bg-rose-100" title="Eliminar">X</button>
                          </div>
                        </th>
                      ));
                      actividadHeaders.push(<th key={`total-header-${dimension.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-3 py-3 text-center text-[10px] font-semibold text-slate-500">Nota</th>);
                      return actividadHeaders;
                    })}
                  </tr>
                </thead>
                <tbody>
                  {estudiantes.map((estudiante) => (
                    <tr key={estudiante.id} className="even:bg-slate-50/40 hover:bg-slate-50">
                      <td className="sticky left-0 z-10 border-b border-r border-slate-200 bg-inherit px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 font-bold text-emerald-700">{estudiante.nombre.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
                          <div className="min-w-0">
                            <p className="truncate text-[11px] font-semibold text-slate-900">{estudiante.nombre}</p>
                            <p className="text-[9px] text-slate-500">{estudiante.id.slice(0, 8)}</p>
                          </div>
                        </div>
                      </td>
                      {dimensiones.map((dimension) => {
                        const groupedActivities = activitiesByDimension[dimension.id] || [];
                        if (autoDimension && dimension.id === autoDimension.id) {
                          const value = autoevaluacion[estudiante.id] ?? getSavedDimensionValue(estudiante.id, dimension.id);
                          return (
                            <td key={`${dimension.id}-${estudiante.id}`} className="border-b border-r border-slate-200 bg-white px-3 py-3">
                              <div className="flex flex-col items-center gap-2">
                                <input type="number" min="0" max={dimension.puntaje_maximo} value={value} onChange={(event) => handleAutoevaluacionChange(estudiante.id, event.target.value)} className="w-20 rounded-2xl border border-slate-200 px-3 py-2 text-center text-[11px] outline-none transition focus:border-blue-300" title="Autoevaluación" />
                                <span className="text-[9px] font-semibold text-slate-500">{getDimensionScore(dimension, estudiante.id)} / {dimension.puntaje_maximo}</span>
                              </div>
                            </td>
                          );
                        }
                        const collapsed = !!collapsedDims[dimension.id];
                        if (collapsed) {
                          return (<td key={`${dimension.id}-total-${estudiante.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center">
                            <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-900 shadow-sm">{getDimensionScore(dimension, estudiante.id)}</span>
                          </td>);
                        }
                        return (
                          <>
                            {groupedActivities.map((actividad, actIndex) => (
                              <td key={`${actividad.id}-${estudiante.id}`} onMouseEnter={() => setHoveredActividad(actividad.id)} onMouseLeave={() => setHoveredActividad(null)} className={`border-b border-r border-slate-200 bg-white px-3 py-3 ${actIndex === 0 ? "border-l-4 border-slate-200 pl-3" : ""} ${hoveredActividad === actividad.id ? "bg-blue-50" : ""}`}>
                                <div className="flex flex-col items-center">
                                  <div className="mb-2 max-w-[140px] text-center text-[10px] font-semibold text-slate-700 truncate">{actividad.nombre}</div>
                                  <input type="number" min="0" max={actividad.puntaje_maximo} value={getActivityValue(actividad.id, estudiante.id)} onChange={(event) => handleActivityValueChange(actividad.id, estudiante.id, event.target.value)} className="w-20 rounded-xl border border-slate-200 px-2 py-2 text-center text-[11px] outline-none transition focus:border-blue-300" title={actividad.nombre} />
                                </div>
                              </td>
                            ))}
                            <td key={`${dimension.id}-total-${estudiante.id}`} className="border-b border-r border-slate-200 bg-slate-50 px-4 py-3 text-center">
                              <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-900 shadow-sm">{getDimensionScore(dimension, estudiante.id)}</span>
                            </td>
                          </>
                        );
                      })}
                      <td className="border-b border-slate-200 bg-slate-950 px-4 py-3 text-center text-white">
                        <span className="text-lg font-black">{getFinalScore(estudiante.id)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="text-lg font-black text-slate-950">Actividades del trimestre</h3>
                <p className="mt-1 text-sm text-slate-500">Pasa el cursor por cada actividad para ver su nombre completo.</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700">{actividades.length} actividades registradas</div>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}


export default CourseDetailPage;
