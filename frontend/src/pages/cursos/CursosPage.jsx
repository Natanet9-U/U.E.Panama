import { useEffect, useMemo, useState } from "react";
import { createCourse, getCoursesPage } from "../../services/coursesService";

const EMPTY_ARRAY = [];

function formatNumber(value) {
  return new Intl.NumberFormat("es-PA").format(Number(value || 0));
}

function StatCard({ item }) {
  const styles = {
    blue: "text-blue-600 bg-blue-50",
    violet: "text-violet-600 bg-violet-50",
    green: "text-emerald-600 bg-emerald-50",
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

function CourseCard({ curso }) {
  const progressWidth = Math.max(10, Math.min(100, curso.progreso || 0));

  return (
    <article className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="border-b border-slate-100 bg-gradient-to-br from-slate-100 via-white to-blue-50 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-blue-600">{curso.codigo}</p>
            <h3 className="mt-2 text-xl font-black text-slate-950">{curso.nombre}</h3>
            <p className="mt-1 text-sm text-slate-600">Prof. {curso.docente}</p>
          </div>
          <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">{curso.estado}</span>
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>Progreso del curso</span>
          <span className="font-bold text-slate-900">{curso.progreso}%</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-slate-100">
          <div className="h-2 rounded-full bg-slate-950" style={{ width: `${progressWidth}%` }} />
        </div>

        <div className="mt-5 space-y-3 text-sm text-slate-600">
          <div className="flex items-center justify-between gap-3">
            <span>Grado</span>
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 font-semibold text-slate-700">{curso.grado}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span>Estudiantes</span>
            <span className="font-semibold text-slate-900">{formatNumber(curso.estudiantes)}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span>Promedio</span>
            <span className="font-semibold text-blue-600">{curso.promedio.toFixed(1)}</span>
          </div>
        </div>

        <div className="mt-5 flex gap-3">
          <button type="button" className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-900 transition hover:bg-slate-50">
            Ver
          </button>
          <button type="button" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-900 transition hover:bg-slate-50">
            ⋮
          </button>
        </div>
      </div>
    </article>
  );
}

function CursosPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({ area_id: "", grado_id: "", docente_id: "" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const resumen = data?.resumen || EMPTY_ARRAY;
  const cursos = data?.cursos || EMPTY_ARRAY;
  const permisos = data?.permisos || { puede_crear: false };
  const catalogos = data?.catalogos || { areas: EMPTY_ARRAY, grados: EMPTY_ARRAY, docentes: EMPTY_ARRAY };
  const paginacion = data?.paginacion || { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 };

  const controls = useMemo(
    () => ({ query, page }),
    [query, page],
  );

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    const timer = window.setTimeout(() => {
      getCoursesPage({ query: controls.query, page: controls.page, pageSize: 6 })
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

          setError(requestError?.response?.data?.error || "No fue posible cargar los cursos");
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

  const handleFieldChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleCreateCourse = async (event) => {
    event.preventDefault();
    setSaving(true);
    setSaveError("");

    try {
      await createCourse(formData);
      setShowCreateForm(false);
      setFormData({ area_id: "", grado_id: "", docente_id: "" });
      setPage(1);
      getCoursesPage({ query, page: 1, pageSize: 6 }).then((response) => setData(response));
    } catch (requestError) {
      setSaveError(requestError?.response?.data?.error || "No fue posible crear el curso");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Cursos</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Administra todos los cursos activos desde datos reales y visibles según tu rol.</p>
          </div>

          {permisos.puede_crear ? (
            <button
              type="button"
              onClick={() => setShowCreateForm((current) => !current)}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:bg-slate-800"
            >
              + Nuevo Curso
            </button>
          ) : null}
        </div>
      </header>

      {error ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div> : null}
      {saveError ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{saveError}</div> : null}

      {showCreateForm && permisos.puede_crear ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h2 className="text-xl font-black text-slate-950">Crear Curso</h2>
          <form onSubmit={handleCreateCourse} className="mt-5 grid gap-4 md:grid-cols-3">
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Asignatura
              <select name="area_id" value={formData.area_id} onChange={handleFieldChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="">Selecciona un área</option>
                {catalogos.areas.map((area) => <option key={area.id} value={area.id}>{area.nombre}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Grado
              <select name="grado_id" value={formData.grado_id} onChange={handleFieldChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="">Selecciona un grado</option>
                {catalogos.grados.map((grado) => <option key={grado.id} value={grado.id}>{grado.nombre}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
              Docente
              <select name="docente_id" value={formData.docente_id} onChange={handleFieldChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none">
                <option value="">Selecciona un docente</option>
                {catalogos.docentes.map((docente) => <option key={docente.id} value={docente.id}>{docente.nombre}</option>)}
              </select>
            </label>
            <div className="md:col-span-3 flex gap-3">
              <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
                {saving ? "Guardando..." : "Crear curso"}
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
          <h2 className="text-xl font-black text-slate-950">Lista de Cursos</h2>
          <div className="relative">
            <svg className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              value={query}
              onChange={handleSearchChange}
              placeholder="Buscar curso..."
              className="w-full min-w-[260px] rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-300 focus:bg-white"
            />
          </div>
        </div>

        <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {loading ? (
            Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-[420px] animate-pulse rounded-[1.75rem] border border-slate-200 bg-slate-100" />
            ))
          ) : cursos.length ? (
            cursos.map((curso) => <CourseCard key={curso.id} curso={curso} />)
          ) : (
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-sm text-slate-500 md:col-span-2 xl:col-span-3">
              No se encontraron cursos para mostrar.
            </div>
          )}
        </div>

        <div className="mt-6 flex flex-col gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between">
          <p>Mostrando {cursos.length} de {formatNumber(paginacion.total)} cursos</p>
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

export default CursosPage;
