import { useEffect, useState } from "react";
import { getSchedulesPage } from "../../services/schedulesService";

const EMPTY_ARRAY = [];

function StatCard({ item }) {
  const toneStyles = {
    blue: "bg-blue-50 text-blue-700",
    violet: "bg-violet-50 text-violet-700",
    emerald: "bg-emerald-50 text-emerald-700",
    orange: "bg-orange-50 text-orange-700",
    slate: "bg-slate-50 text-slate-700",
  };

  const iconBgStyles = {
    blue: "bg-blue-100",
    violet: "bg-violet-100",
    emerald: "bg-emerald-100",
    orange: "bg-orange-100",
    slate: "bg-slate-100",
  };

  const tone = item.acento || "slate";

  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500">{item.titulo}</p>
          <p className="mt-2 text-4xl font-black text-slate-950">{item.valor}</p>
          <p className="mt-1 text-xs text-slate-500">{item.detalle}</p>
        </div>
        <div className={`rounded-full ${iconBgStyles[tone]} p-3`}>
          <span className={`block text-xl ${toneStyles[tone]}`}>
            {item.icono === "calendar" && "📅"}
            {item.icono === "clock" && "🕐"}
            {item.icono === "building" && "🏢"}
            {item.icono === "users" && "👥"}
          </span>
        </div>
      </div>
    </article>
  );
}

function ClassCard({ clase }) {
  if (!clase || Object.keys(clase).length === 0) return null;

  const colors = {
    "Matemáticas": "border-blue-200 bg-blue-50 text-blue-900",
    "Historia": "border-purple-200 bg-purple-50 text-purple-900",
    "Química": "border-pink-200 bg-pink-50 text-pink-900",
    "Física": "border-green-200 bg-green-50 text-green-900",
    "Inglés": "border-cyan-200 bg-cyan-50 text-cyan-900",
  };

  const colorClass = colors[clase.asignatura] || "border-slate-200 bg-slate-50 text-slate-900";

  return (
    <div className={`rounded-3xl border-2 ${colorClass} p-4`}>
      <p className="text-sm font-bold">{clase.asignatura}</p>
      <p className="mt-1 flex items-center gap-1 text-xs">
        <span>⏰</span>
        {clase.hora_fin ? `${clase.hora_fin} - ${clase.hora_fin}` : clase.hora_fin}
      </p>
      <p className="mt-1 flex items-center gap-1 text-xs">
        <span>📍</span>
        {clase.aula}
      </p>
      <p className="mt-1 flex items-center gap-1 text-xs">
        <span>👥</span>
        {clase.estudiantes} estudiantes
      </p>
    </div>
  );
}

function UpcomingClassRow({ clase }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 transition hover:bg-slate-50">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-950">{clase.fecha}</span>
            <span className="text-xs text-slate-500">{clase.dia}</span>
          </div>
          <p className="mt-1 text-lg font-black text-slate-950">{clase.asignatura}</p>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
            <span>⏰ {clase.hora}</span>
            <span>🏢 {clase.grado}</span>
            <span>📍 {clase.aula}</span>
            <span>👨‍🏫 {clase.docente}</span>
          </div>
        </div>
        <button
          type="button"
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          Ver detalles
        </button>
      </div>
    </article>
  );
}

function HorariosPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getSchedulesPage({})
      .then((response) => {
        if (!mounted) return;
        setData(response);
        setError("");
      })
      .catch((requestError) => {
        if (!mounted) return;
        setError(
          requestError?.response?.data?.error || "No fue posible cargar los horarios"
        );
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

  const resumen = data?.resumen || EMPTY_ARRAY;
  const calendario = data?.calendario || EMPTY_ARRAY;
  const proximasClases = data?.proximas_clases || EMPTY_ARRAY;

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Horarios</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">
              Visualiza y organiza tu calendario académico
            </p>
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <button
              type="button"
              className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              ⬇️ Exportar
            </button>
            <button
              type="button"
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-200 transition hover:bg-slate-800"
            >
              ➕ Nueva Clase
            </button>
          </div>
        </div>
      </header>

      {error ? (
        <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-36 animate-pulse rounded-3xl bg-slate-200"
              />
            ))
          : resumen.map((item) => <StatCard key={item.titulo} item={item} />)}
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950">Calendario Semanal</h2>
        <div className="mt-6 overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">
                  Hora
                </th>
                {["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"].map(
                  (day) => (
                    <th
                      key={day}
                      className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wide text-slate-600"
                    >
                      {day}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="6"
                    className="px-4 py-8 text-center text-sm text-slate-500"
                  >
                    Cargando calendario...
                  </td>
                </tr>
              ) : calendario.length > 0 ? (
                calendario.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-4 text-sm font-semibold text-slate-900">
                      {row.hora}
                    </td>
                    {["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"].map(
                      (day) => (
                        <td
                          key={day}
                          className="px-4 py-4 text-center"
                        >
                          <div className="flex flex-col gap-2">
                            {row.clases[day]?.map((clase, i) => (
                              <ClassCard key={i} clase={clase} />
                            ))}
                          </div>
                        </td>
                      )
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan="6"
                    className="px-4 py-8 text-center text-sm text-slate-500"
                  >
                    No hay clases programadas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950">Próximas Clases</h2>
        <div className="mt-6 space-y-3">
          {loading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 animate-pulse rounded-2xl bg-slate-100"
                />
              ))
            : proximasClases.length > 0
            ? proximasClases.map((clase, idx) => (
                <UpcomingClassRow key={idx} clase={clase} />
              ))
            : <p className="text-sm text-slate-500">No hay clases próximas.</p>}
        </div>
      </section>
    </section>
  );
}

export default HorariosPage;
