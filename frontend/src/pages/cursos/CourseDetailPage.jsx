import { useEffect, useState, useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { getCourseDetail, updateGrades } from "../../services/coursesService";
import { getAttendance, markAttendance } from "../../services/attendanceService";
import activitiesService from "../../services/activitiesService";

function CourseDetailPage() {
  const [search] = useSearchParams();
  const asignacionId = search.get("asignacion_id");
  const [periodoId, setPeriodoId] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [data, setData] = useState(null);
  const [attendance, setAttendance] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState("attendance");
  const [actividades, setActividades] = useState([]);
  const [actividadesNotas, setActividadesNotas] = useState({});
  const [nuevoActividad, setNuevoActividad] = useState({ nombre: "", puntaje_maximo: 100 });
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    if (!asignacionId) return;
    setLoading(true);
    getCourseDetail({ asignacionId, periodoId, fecha })
      .then((resp) => setData(resp))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [asignacionId, periodoId, fecha]);

  useEffect(() => {
    if (!asignacionId) return;
    getAttendance({ asignacionId, fecha }).then((resp) => {
      const map = {};
      (resp.asistencias || []).forEach((a) => { map[a.estudiante_id] = a.estado; });
      setAttendance(map);
    }).catch(() => setAttendance({}));
  }, [asignacionId, fecha]);

  useEffect(() => {
    if (!asignacionId) return;
    activitiesService.getActividades({ asignacionId })
      .then((resp) => setActividades(resp.actividades || []))
      .catch(() => setActividades([]));
  }, [asignacionId]);

  useEffect(() => {
    if (!asignacionId) return;
    if (data && data.actividad_notas) {
      setActividadesNotas(data.actividad_notas || {});
    }
  }, [asignacionId, actividades]);

  const toggleAttendance = (estId) => {
    setAttendance((cur) => ({ ...cur, [estId]: cur[estId] === "present" ? "absent" : "present" }));
  };

  const submitAttendance = async () => {
    setSaving(true);
    const estados = {};
    Object.entries(attendance).forEach(([k, v]) => { estados[k] = v || "absent"; });
    try {
      await markAttendance({ asignacionId, fecha, estados });
      alert("Asistencias guardadas");
    } catch (err) {
      alert(err?.response?.data?.error || "Error al guardar asistencia");
    } finally { setSaving(false); }
  };

  const agregarActividad = async () => {
    if (!nuevoActividad.nombre) return alert("Ingresa el nombre de la actividad");
    setSaving(true);
    try {
      await activitiesService.createActividad({ asignacionId, ...nuevoActividad });
      setNuevoActividad({ nombre: "", tipo: "tarea", puntaje_maximo: 100 });
      const resp = await activitiesService.getActividades({ asignacionId });
      setActividades(resp.actividades || []);
      alert("Actividad creada");
    } catch (err) {
      alert(err?.response?.data?.error || "Error al crear actividad");
    } finally { setSaving(false); }
  };

  const setNotaActividad = (actividadId, estId, valor) => {
    setActividadesNotas((cur) => ({
      ...cur,
      [actividadId]: { ...(cur[actividadId] || {}), [estId]: parseInt(valor) || 0 },
    }));
  };

  const computeStudentActivityAverage = (estId) => {
    let totalVal = 0;
    let totalMax = 0;
    (actividades || []).forEach((act) => {
      const val = actividadesNotas[act.id]?.[estId];
      if (val !== undefined) {
        totalVal += Number(val || 0);
        totalMax += Number(act.puntaje_maximo || 0);
      }
    });
    if (!totalMax) return 0;
    return Math.round((totalVal / totalMax) * 100);
  };

  const submitAllActividadesNotas = async () => {
    setSavingAll(true);
    try {
      await Promise.all((actividades || []).map((act) => activitiesService.updateActividadesNotas({ asignacionId, actividadId: act.id, notas: actividadesNotas[act.id] || {} })));
      alert("Todas las notas guardadas");
    } catch (err) {
      alert(err?.response?.data?.error || "Error al guardar notas");
    } finally {
      setSavingAll(false);
    }
  };

  const submitActividadesNotas = async (actividadId) => {
    setSaving(true);
    try {
      const notas = actividadesNotas[actividadId] || {};
      await activitiesService.updateActividadesNotas({ asignacionId, actividadId, notas });
      alert("Notas de actividad guardadas");
    } catch (err) {
      alert(err?.response?.data?.error || "Error al guardar notas");
    } finally { setSaving(false); }
  };

  if (!asignacionId) return <div>Asignación no especificada</div>;
  if (loading) return <div>Cargando...</div>;

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Detalle del Curso</h1>
      </header>

      <div className="border-b">
        <div className="flex gap-4">
          <button onClick={() => setTab("attendance")} className={`px-4 py-2 ${tab === "attendance" ? "border-b-2 border-blue-600 font-bold" : ""}`}>Asistencia</button>
          <button onClick={() => setTab("grades")} className={`px-4 py-2 ${tab === "grades" ? "border-b-2 border-blue-600 font-bold" : ""}`}>Notas</button>
        </div>
      </div>

      {tab === "attendance" && (
        <div className="space-y-4">
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm font-semibold mb-2">Fecha</label>
              <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} className="rounded-md border px-3 py-2" />
            </div>
            <div className="ml-auto">
              <button onClick={submitAttendance} disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-white shadow">Guardar Asistencia</button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gradient-to-r from-slate-50 to-white">
                  <th className="px-4 py-3 text-left">Estudiante</th>
                  <th className="px-4 py-3 text-center">Estado</th>
                </tr>
              </thead>
              <tbody>
                {(data.estudiantes || []).map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-semibold">{s.nombre.split(' ').map(n=>n[0]).slice(0,2).join('')}</div>
                      <div>
                        <div className="font-medium">{s.nombre}</div>
                        <div className="text-xs text-slate-500">{s.id.slice(0,8)}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => toggleAttendance(s.id)} className={`px-4 py-1 rounded-full font-semibold inline-flex items-center gap-2 ${attendance[s.id] === "present" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
                        {attendance[s.id] === "present" ? '✅ Presente' : '❌ Ausente'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "grades" && (
        <div className="space-y-6">
          <div className="border rounded-lg p-4 bg-slate-50">
            <h3 className="font-semibold mb-4">Agregar Actividad</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="block text-sm font-semibold mb-1">Nombre de la Actividad</label>
                <input placeholder="Ej: Práctica 1, Tarea 3, Quiz..." value={nuevoActividad.nombre} onChange={(e) => setNuevoActividad({ ...nuevoActividad, nombre: e.target.value })} className="rounded border px-3 py-2 w-full text-sm" />
                <p className="text-xs text-slate-500 mt-1">El nombre identifica la actividad (Práctica, Tarea, Examen, etc.)</p>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Puntaje Máximo</label>
                <input type="number" placeholder="100" min="1" value={nuevoActividad.puntaje_maximo} onChange={(e) => setNuevoActividad({ ...nuevoActividad, puntaje_maximo: parseInt(e.target.value) || 100 })} className="rounded border px-3 py-2 w-full text-sm" />
                <p className="text-xs text-slate-500 mt-1">Puntos totales posibles para esta actividad</p>
              </div>
              <div className="flex items-end">
                <button onClick={agregarActividad} disabled={saving} className="rounded bg-green-600 px-4 py-2 text-white shadow w-full">Agregar Actividad</button>
              </div>
            </div>
          </div>
          {actividades.length === 0 ? (
            <div className="text-center text-slate-500">No hay actividades. Agrega una para comenzar.</div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <h3 className="text-lg font-semibold">Actividades ({actividades.length})</h3>
                <button onClick={submitAllActividadesNotas} disabled={savingAll} className="ml-auto rounded bg-indigo-600 px-4 py-2 text-white shadow">Guardar Todo</button>
              </div>

              {actividades.map((actividad) => (
                <div key={actividad.id} className="border rounded-lg p-4 bg-white shadow-sm">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{actividad.nombre}</h4>
                    <div className="text-sm text-slate-500">Puntaje: {actividad.puntaje_maximo}</div>
                  </div>
                  <div className="overflow-x-auto mt-4">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-slate-50">
                          <th className="px-4 py-2 text-left">Estudiante</th>
                          <th className="px-4 py-2 text-left">
                            <div>Progreso General</div>
                            <p className="text-xs text-slate-500 font-normal">% promedio en todas las actividades</p>
                          </th>
                          <th className="px-4 py-2 text-center">
                            <div>Nota en {actividad.nombre}</div>
                            <p className="text-xs text-slate-500 font-normal">De 0 a {actividad.puntaje_maximo}</p>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {(data.estudiantes || []).map((s) => (
                          <tr key={s.id} className="hover:bg-slate-50">
                            <td className="px-4 py-2 flex items-center gap-3">
                              <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-semibold">{s.nombre.split(' ').map(n=>n[0]).slice(0,2).join('')}</div>
                              <div>
                                <div className="font-medium">{s.nombre}</div>
                                <div className="text-xs text-slate-400">{s.id.slice(0,8)}</div>
                              </div>
                            </td>
                            <td className="px-4 py-2">
                              <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                                <div className={`h-3 rounded-full bg-gradient-to-r from-green-400 to-emerald-600`} style={{ width: `${computeStudentActivityAverage(s.id)}%` }} />
                              </div>
                              <div className="text-xs text-slate-500 mt-1">{computeStudentActivityAverage(s.id)}%</div>
                            </td>
                            <td className="px-4 py-2 text-center">
                              <div className="inline-block">
                                <input type="number" min="0" max={actividad.puntaje_maximo} value={actividadesNotas[actividad.id]?.[s.id] ?? 0} onChange={(e) => setNotaActividad(actividad.id, s.id, e.target.value)} className="w-24 rounded border-2 border-blue-300 px-2 py-1 text-center shadow-sm focus:border-blue-500 focus:outline-none" />
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-4 text-right">
                    <button onClick={() => submitActividadesNotas(actividad.id)} disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-white">Guardar Notas</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default CourseDetailPage;
