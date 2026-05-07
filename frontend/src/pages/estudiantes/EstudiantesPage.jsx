import { useEffect, useMemo, useState } from "react";
import { createStudent, getStudentsPage } from "../../services/studentsService";

const EMPTY_ARRAY = [];

function formatNumber(value) {
  return new Intl.NumberFormat("es-PA").format(Number(value || 0));
}

function StatCard({ item }) {
  const styles = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-emerald-600 bg-emerald-50",
    violet: "text-violet-600 bg-violet-50",
    orange: "text-orange-600 bg-orange-50",
  };

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <h3 className="text-sm font-semibold text-slate-500">{item.titulo}</h3>
      <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{item.valor}</p>
      <p className="mt-2 text-sm text-slate-500">{item.detalle}</p>
      <div className={`mt-4 inline-flex rounded-2xl px-3 py-2 text-xs font-semibold ${styles[item.acento] || styles.blue}`}>
        {item.titulo}
      </div>
    </article>
  );
}

function StudentRow({ estudiante }) {
  const statusClass = estudiante.estado_clase === "Activo"
    ? "bg-emerald-100 text-emerald-700"
    : "bg-slate-100 text-slate-700";

  const progressColor = estudiante.asistencia >= 90 ? "bg-emerald-500" : estudiante.asistencia >= 80 ? "bg-blue-500" : "bg-orange-500";

  return (
    <tr className="border-b border-slate-100 last:border-b-0">
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
            {estudiante.avatar}
          </div>
          <div>
            <p className="text-sm font-bold text-slate-950">{estudiante.nombre}</p>
            <p className="text-xs text-slate-500">ID: {estudiante.codigo}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-slate-600">
        <p>{estudiante.email || "-"}</p>
        <p className="mt-1">{estudiante.telefono}</p>
      </td>
      <td className="px-4 py-4">
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
          {estudiante.grado.nombre}
        </span>
      </td>
      <td className="px-4 py-4 text-sm font-semibold text-blue-600">{estudiante.promedio.toFixed(1)}</td>
      <td className="px-4 py-4 text-sm text-slate-600">
        <div className="flex items-center gap-3">
          <div className="h-2 w-24 rounded-full bg-slate-100">
            <div className={`h-2 rounded-full ${progressColor}`} style={{ width: `${estudiante.asistencia}%` }} />
          </div>
          <span>{estudiante.asistencia}%</span>
        </div>
      </td>
      <td className="px-4 py-4">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}>
          {estudiante.estado_clase}
        </span>
      </td>
      <td className="px-4 py-4 text-right text-slate-400">
        <button type="button" className="rounded-full px-2 py-1 hover:bg-slate-100" aria-label={`Acciones de ${estudiante.nombre}`}>
          ⋮
        </button>
      </td>
    </tr>
  );
}

function EstudiantesPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [gradoId, setGradoId] = useState("");
  const [page, setPage] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [formData, setFormData] = useState({
    nombres: "",
    primer_apellido: "",
    segundo_apellido: "",
    email: "",
    ci: "",
    telefono: "",
    grado_id: "",
    genero: "",
    estado: "Activo",
  });

  const resumen = data?.resumen || EMPTY_ARRAY;
  const estudiantes = data?.estudiantes || EMPTY_ARRAY;
  const grados = data?.filtros?.grados || EMPTY_ARRAY;
  const permisos = data?.permisos || { puede_crear: false };
  const paginacion = data?.paginacion || { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 };

  const controls = useMemo(
    () => ({ query, gradoId, page }),
    [query, gradoId, page],
  );

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    const timer = window.setTimeout(() => {
      getStudentsPage({ query: controls.query, gradoId: controls.gradoId, page: controls.page, pageSize: 8 })
        .then((response) => {
          if (!mounted) {
            return;
          }

          setData(response);
          setError("");
          if (!response?.permisos?.puede_crear) {
            setShowCreateForm(false);
          }
        })
        .catch((requestError) => {
          if (!mounted) {
            return;
          }

          setError(requestError?.response?.data?.error || "No fue posible cargar los estudiantes");
        })
        .finally(() => {
          if (mounted) {
            setLoading(false);
          }
        });
    }, 250);

    return () => {
      mounted = false;
      window.clearTimeout(timer);
    };
  }, [controls]);

  const handleSearchChange = (event) => {
    setQuery(event.target.value);
    setPage(1);
  };

  const handleGradeChange = (event) => {
    setGradoId(event.target.value);
    setPage(1);
  };

  const handleFormChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleCreateStudent = async (event) => {
    event.preventDefault();
    setSaving(true);
    setSaveError("");

    try {
      await createStudent(formData);
      setShowCreateForm(false);
      setFormData({
        nombres: "",
        primer_apellido: "",
        segundo_apellido: "",
        email: "",
        ci: "",
        telefono: "",
        grado_id: "",
        genero: "",
        estado: "Activo",
      });
      setPage(1);
      getStudentsPage({ query, gradoId, page: 1, pageSize: 8 }).then((response) => setData(response));
    } catch (requestError) {
      setSaveError(requestError?.response?.data?.error || "No fue posible crear el estudiante");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(255,255,255,0.94),rgba(99,102,241,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Estudiantes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Gestiona y monitorea a todos los estudiantes desde datos reales de la base.</p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button type="button" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-900 shadow-sm transition hover:bg-slate-50">
              Exportar
            </button>
            {permisos.puede_crear ? (
              <button
                type="button"
                onClick={() => setShowCreateForm((current) => !current)}
                className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:bg-slate-800"
              >
                Nuevo Estudiante
              </button>
            ) : null}
          </div>
        </div>
      </header>

      {error ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div> : null}
      {saveError ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{saveError}</div> : null}

      {showCreateForm && permisos.puede_crear ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Crear Estudiante</h2>
          <form onSubmit={handleCreateStudent} className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Nombres
              <input name="nombres" value={formData.nombres} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Primer apellido
              <input name="primer_apellido" value={formData.primer_apellido} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Segundo apellido
              <input name="segundo_apellido" value={formData.segundo_apellido} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Email
              <input name="email" type="email" value={formData.email} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              CI
              <input name="ci" value={formData.ci} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Teléfono
              <input name="telefono" value={formData.telefono} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Grado
              <select name="grado_id" value={formData.grado_id} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="">Selecciona un grado</option>
                {grados.map((grado) => <option key={grado.id} value={grado.id}>{grado.nombre}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Género
              <select name="genero" value={formData.genero} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="">Sin definir</option>
                <option value="M">Masculino</option>
                <option value="F">Femenino</option>
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Estado
              <select name="estado" value={formData.estado} onChange={handleFormChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
              </select>
            </label>
            <div className="md:col-span-2 xl:col-span-3 flex gap-3">
              <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
                {saving ? "Guardando..." : "Crear estudiante"}
              </button>
              <button type="button" onClick={() => setShowCreateForm(false)} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-900">
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {resumen.map((item) => (
          <StatCard key={item.titulo} item={item} />
        ))}
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950">Lista de Estudiantes</h2>
            <p className="mt-1 text-sm text-slate-500">{paginacion.total} estudiantes en total</p>
          </div>

          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative">
              <svg className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <input
                value={query}
                onChange={handleSearchChange}
                placeholder="Buscar por nombre o email..."
                className="w-full min-w-[280px] rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
              />
            </div>

            <select
              value={gradoId}
              onChange={handleGradeChange}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white"
            >
              <option value="">Todos los grados</option>
              {grados.map((grado) => (
                <option key={grado.id} value={grado.id}>{grado.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estudiante</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Contacto</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Grado</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Promedio</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Asistencia</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-600">Estado</th>
                  <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wide text-slate-600">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {loading ? (
                  Array.from({ length: 4 }).map((_, index) => (
                    <tr key={index}>
                      <td className="px-4 py-4" colSpan="7">
                        <div className="h-16 animate-pulse rounded-2xl bg-slate-100" />
                      </td>
                    </tr>
                  ))
                ) : estudiantes.length ? (
                  estudiantes.map((estudiante) => <StudentRow key={estudiante.id} estudiante={estudiante} />)
                ) : (
                  <tr>
                    <td className="px-4 py-10 text-center text-sm text-slate-500" colSpan="7">
                      No se encontraron estudiantes con esos filtros.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
          <p>Mostrando {estudiantes.length} de {formatNumber(paginacion.total)} estudiantes</p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={!paginacion.anterior || loading}
              onClick={() => setPage((currentPage) => Math.max(currentPage - 1, 1))}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="rounded-2xl bg-slate-100 px-4 py-2 font-semibold text-slate-700">
              Página {paginacion.pagina} de {paginacion.paginas}
            </span>
            <button
              type="button"
              disabled={!paginacion.siguiente || loading}
              onClick={() => setPage((currentPage) => currentPage + 1)}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </section>
    </section>
  );
}

export default EstudiantesPage;
