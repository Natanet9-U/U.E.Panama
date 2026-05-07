import { useEffect, useMemo, useState } from "react";
import { getCurrentUser, getStoredUser } from "../../services/authService";
import { getDashboardData } from "../../services/dashboardService";
import LineChartMock from "../../components/charts/LineChartMock";
import BarChartMock from "../../components/charts/BarChartMock";
import PieChartMock from "../../components/charts/PieChartMock";

const EMPTY_ARRAY = [];

function formatNumber(value) {
  return new Intl.NumberFormat("es-PA").format(Number(value || 0));
}

function StatCard({ item }) {
  const iconByTone = {
    blue: "text-blue-600 bg-blue-50",
    violet: "text-violet-600 bg-violet-50",
    green: "text-emerald-600 bg-emerald-50",
    orange: "text-orange-600 bg-orange-50",
  };

  const styles = iconByTone[item.acento] || iconByTone.blue;
  const icon = {
    blue: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="10" cy="7" r="4" />
        <path d="M19 8v6" />
        <path d="M16 11h6" />
      </svg>
    ),
    violet: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 4h16v16H4z" />
        <path d="M8 9h8M8 13h8" />
      </svg>
    ),
    green: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M4 16l6-6 4 4 6-8" />
        <path d="M14 6h6v6" />
      </svg>
    ),
    orange: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6">
        <path d="M20 12a8 8 0 1 1-4.5-7.2" />
        <path d="M20 4v5h-5" />
      </svg>
    ),
  };

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{item.titulo}</h3>
          <p className="mt-5 text-4xl font-black tracking-tight text-slate-950">{item.valor}</p>
          <p className="mt-2 text-sm text-slate-500">{item.detalle}</p>
        </div>
        <div className={`rounded-2xl p-3 ${styles}`}>{icon[item.acento] || icon.blue}</div>
      </div>
    </article>
  );
}

function DashboardPage() {
  const [usuario, setUsuario] = useState(getStoredUser());
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const resumen = dashboard?.resumen || EMPTY_ARRAY;
  const asistenciaSemanal = dashboard?.asistencia_semanal || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const promedioPorAsignatura = dashboard?.promedio_por_asignatura || { labels: EMPTY_ARRAY, data: EMPTY_ARRAY };
  const rendimiento = dashboard?.rendimiento ?? EMPTY_ARRAY;
  const proximasClases = dashboard?.proximas_clases || EMPTY_ARRAY;
  const actividadReciente = dashboard?.actividad_reciente || EMPTY_ARRAY;
  const tareasPendientes = dashboard?.tareas_pendientes || { cantidad: 0, mensaje: "", detalle: "" };
  const estudiantesDestacados = dashboard?.estudiantes_destacados || [];

  const rendimientoSegmentos = useMemo(
    () => [
      { label: "Excelente", value: rendimiento.find((item) => item.label === "Excelente")?.value || 0, color: "#10b981", description: "Promedios sobresalientes" },
      { label: "Bueno", value: rendimiento.find((item) => item.label === "Bueno")?.value || 0, color: "#3b82f6", description: "Buen nivel académico" },
      { label: "Regular", value: rendimiento.find((item) => item.label === "Regular")?.value || 0, color: "#f59e0b", description: "En seguimiento" },
      { label: "Deficiente", value: rendimiento.find((item) => item.label === "Deficiente")?.value || 0, color: "#ef4444", description: "Requiere refuerzo" },
    ],
    [rendimiento],
  );

  useEffect(() => {
    let mounted = true;

    setLoading(true);

    Promise.all([getDashboardData(), getCurrentUser()])
      .then(([dashboardResponse, user]) => {
        if (!mounted) {
          return;
        }

        setDashboard(dashboardResponse);
        setUsuario(user);
        setError("");
      })
      .catch((requestError) => {
        if (!mounted) {
          return;
        }

        setError(requestError?.response?.data?.error || "No fue posible cargar el dashboard");
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const greetingName = usuario ? `${usuario.nombre}` : "";

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(59,130,246,0.08),rgba(139,92,246,0.06),rgba(255,255,255,0.92))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
        <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-slate-950">Dashboard</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">
              Bienvenido de nuevo{greetingName ? `, ${greetingName}` : ""}, aquí está el resumen de hoy.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-slate-500">
            <span className="rounded-full border border-slate-200 bg-white px-4 py-2">{dashboard?.periodo_activo ? `${dashboard.periodo_activo.nombre} ${dashboard.periodo_activo.gestion}` : "Periodo no definido"}</span>
            <span className="rounded-full border border-slate-200 bg-white px-4 py-2">{resumen.length} indicadores en vivo</span>
          </div>
        </div>
      </header>

      {error ? (
        <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div>
      ) : null}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-36 animate-pulse rounded-3xl border border-slate-200 bg-white" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {resumen.map((item) => (
            <StatCard key={item.titulo} item={item} />
          ))}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Asistencia Semanal</h2>
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">Fuente: base de datos</span>
          </div>
          <div className="mt-6 h-72 rounded-3xl border border-slate-100 bg-slate-50 p-4">
            <LineChartMock data={asistenciaSemanal.data} labels={asistenciaSemanal.labels} color="#3b82f6" />
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Promedio por Asignatura</h2>
            <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">Promedio de notas</span>
          </div>
          <div className="mt-6 h-72 rounded-3xl border border-slate-100 bg-slate-50 p-4">
            <BarChartMock data={promedioPorAsignatura.data} labels={promedioPorAsignatura.labels} color="#8b5cf6" />
          </div>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.95fr_0.95fr]">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Distribución de Rendimiento</h2>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Top académico</span>
          </div>
          <div className="mt-6">
            <PieChartMock segments={rendimientoSegmentos} title="Rendimiento" />
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Próximas Clases</h2>
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">Asignaciones</span>
          </div>
          <div className="mt-6 space-y-3">
            {proximasClases.length ? proximasClases.map((item) => (
              <article key={`${item.titulo}-${item.detalle}`} className="rounded-2xl bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-base font-bold text-slate-950">{item.titulo}</p>
                    <p className="mt-1 text-sm text-slate-600">{item.detalle}</p>
                    <p className="mt-1 text-xs font-medium text-slate-400">{item.subdetalle}</p>
                  </div>
                  <div className="rounded-2xl bg-white px-3 py-2 text-right shadow-sm">
                    <p className="text-xs text-slate-400">Estudiantes</p>
                    <p className="text-lg font-black text-slate-950">{formatNumber(item.estudiantes)}</p>
                  </div>
                </div>
              </article>
            )) : <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No hay clases registradas para mostrar.</p>}
          </div>
          <button className="mt-5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-900 transition hover:border-slate-300 hover:bg-slate-50">Ver horario completo</button>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Actividad Reciente</h2>
            <span className="rounded-full bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-700">Últimos cambios</span>
          </div>
          <div className="mt-6 space-y-4">
            {actividadReciente.length ? actividadReciente.map((item) => (
              <article key={`${item.persona}-${item.detalle}`} className="flex items-start gap-3 rounded-2xl bg-slate-50 p-4">
                <div className={`mt-1 h-10 w-10 rounded-full ${item.estado === "warning" ? "bg-orange-100" : "bg-emerald-100"}`} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-slate-950">{item.persona}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.detalle}</p>
                  <p className="mt-1 text-xs text-slate-400">{item.tiempo}</p>
                </div>
                <span className={`mt-1 h-3 w-3 rounded-full ${item.estado === "warning" ? "bg-orange-500" : "bg-emerald-500"}`} />
              </article>
            )) : <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">Aún no hay actividad reciente.</p>}
          </div>
          <button className="mt-5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-900 transition hover:border-slate-300 hover:bg-slate-50">Ver todas las actividades</button>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2rem] border border-orange-200 bg-orange-50/70 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center gap-3 text-orange-700">
            <span className="rounded-full border border-orange-200 bg-white p-2 text-orange-600">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                <path d="M12 8v5" />
                <path d="M12 16h.01" />
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3l-8.47-14.14a2 2 0 0 0-3.42 0Z" />
              </svg>
            </span>
            <h2 className="text-xl font-black text-orange-900">Tareas Pendientes de Revisar</h2>
          </div>
          <p className="mt-6 max-w-2xl text-base text-orange-800">{tareasPendientes.mensaje} {tareasPendientes.detalle}</p>
          <button className="mt-6 rounded-2xl bg-orange-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-orange-200 transition hover:bg-orange-500">Revisar ahora</button>
        </section>

        <section className="rounded-[2rem] border border-blue-200 bg-blue-50/70 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center gap-3 text-blue-700">
            <span className="rounded-full border border-blue-200 bg-white p-2 text-blue-600">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                <path d="M12 12v7" />
                <path d="M9 15l3-3 3 3" />
                <path d="M8 5.5A4.5 4.5 0 0 1 12.5 1h0A4.5 4.5 0 0 1 17 5.5V7h1.5A2.5 2.5 0 0 1 21 9.5v8A2.5 2.5 0 0 1 18.5 20H5.5A2.5 2.5 0 0 1 3 17.5v-8A2.5 2.5 0 0 1 5.5 7H7V5.5Z" />
              </svg>
            </span>
            <h2 className="text-xl font-black text-blue-900">Estudiantes Destacados</h2>
          </div>
          <p className="mt-6 text-base text-blue-800">{estudiantesDestacados.length} estudiantes han obtenido calificaciones sobresalientes este mes.</p>
          <div className="mt-5 space-y-3">
            {estudiantesDestacados.length ? estudiantesDestacados.map((item) => (
              <article key={item.nombre} className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 shadow-sm">
                <div>
                  <p className="text-sm font-bold text-slate-950">{item.nombre}</p>
                  <p className="text-xs text-slate-500">{item.mensaje}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-black text-blue-700">{item.promedio}</p>
                  <p className="text-xs text-slate-400">Promedio</p>
                </div>
              </article>
            )) : <p className="rounded-2xl bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">No hay estudiantes destacados registrados.</p>}
          </div>
          <button className="mt-5 rounded-2xl border border-blue-300 bg-white px-5 py-3 text-sm font-bold text-blue-700 transition hover:bg-blue-100">Ver detalles</button>
        </section>
      </div>
    </section>
  );
}

export default DashboardPage;
