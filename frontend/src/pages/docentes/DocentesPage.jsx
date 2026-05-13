import { useEffect, useMemo, useState } from "react";
import { createDocente, getDocentesPage } from "../../services/docentesService";

const EMPTY_ARRAY = [];

function DocenteCard({ docente }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-black text-slate-950">{docente.nombre}</h3>
          <p className="mt-1 text-sm text-slate-500">{docente.email}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${docente.activo ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
          {docente.activo ? "Activo" : "Inactivo"}
        </span>
      </div>

      <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
        <p><span className="font-semibold text-slate-900">CI:</span> {docente.ci || "-"}</p>
        <p><span className="font-semibold text-slate-900">Teléfono:</span> {docente.telefono}</p>
        <p><span className="font-semibold text-slate-900">Título:</span> {docente.titulo_academico}</p>
        <p><span className="font-semibold text-slate-900">Especialidad:</span> {docente.especialidad}</p>
      </div>
    </article>
  );
}

function DocentesPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState({
    nombres: "",
    apellido: "",
    ci: "",
    telefono: "",
    titulo_academico: "",
    especialidad: "",
    anos_experiencia: "",
  });

  const docentes = data?.docentes || EMPTY_ARRAY;
  const paginacion = data?.paginacion || { pagina: 1, paginas: 1, anterior: false, siguiente: false, total: 0 };
  const permisos = data?.permisos || { puede_crear: false };

  const controls = useMemo(() => ({ query, page }), [query, page]);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getDocentesPage({ query: controls.query, page: controls.page, pageSize: 8 })
      .then((response) => {
        if (!mounted) return;
        setData(response);
        setError("");
      })
      .catch((requestError) => {
        if (!mounted) return;
        setError(requestError?.response?.data?.error || "No fue posible cargar los docentes");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [controls]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setSaveError("");
    setSaveSuccess("");

    try {
      const response = await createDocente(formData);
      setSaveSuccess(`${response.mensaje}. Usuario temporal: ${response.docente.usuario_temporal}`);
      setFormData({
        nombres: "",
        apellido: "",
        ci: "",
        telefono: "",
        titulo_academico: "",
        especialidad: "",
        anos_experiencia: "",
      });
      setPage(1);
      getDocentesPage({ query, page: 1, pageSize: 8 }).then((responseData) => setData(responseData));
    } catch (requestError) {
      setSaveError(requestError?.response?.data?.error || "No fue posible crear el docente");
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
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Docentes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Crea docentes con un usuario único que termina en @uepanama, aunque tengan el mismo nombre y apellido.</p>
          </div>
        </div>
      </header>

      {error ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div> : null}
      {saveError ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{saveError}</div> : null}
      {saveSuccess ? <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">{saveSuccess}</div> : null}

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950">Crear docente</h2>
            <p className="mt-1 text-sm text-slate-500">El sistema genera un email único como nombre.apellido.XXXXXX@uepanama.</p>
          </div>
          <div className="text-sm text-slate-500">{permisos.puede_crear ? "Con permiso para crear" : "Sin permiso de creación"}</div>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Nombres
            <input name="nombres" value={formData.nombres} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Apellido
            <input name="apellido" value={formData.apellido} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            CI
            <input name="ci" value={formData.ci} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Teléfono
            <input name="telefono" value={formData.telefono} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Título académico
            <input name="titulo_academico" value={formData.titulo_academico} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Especialidad
            <input name="especialidad" value={formData.especialidad} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
            Años de experiencia
            <input name="anos_experiencia" type="number" value={formData.anos_experiencia} onChange={handleChange} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
          </label>

          <div className="md:col-span-2 xl:col-span-3 flex gap-3">
            <button type="submit" disabled={saving} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">
              {saving ? "Guardando..." : "Crear docente"}
            </button>
            <button type="button" onClick={() => setFormData({ nombres: "", apellido: "", ci: "", telefono: "", titulo_academico: "", especialidad: "", anos_experiencia: "" })} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-900">
              Limpiar
            </button>
          </div>
        </form>
      </section>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-black text-slate-950">Docentes registrados</h2>
            <p className="mt-1 text-sm text-slate-500">{paginacion.total} docentes en total</p>
          </div>
          <input
            value={query}
            onChange={(event) => { setQuery(event.target.value); setPage(1); }}
            placeholder="Buscar por nombre, CI o email..."
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none"
          />
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {loading ? (
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">Cargando docentes...</div>
          ) : docentes.length ? (
            docentes.map((docente) => <DocenteCard key={docente.id} docente={docente} />)
          ) : (
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500 lg:col-span-2">No hay docentes para mostrar.</div>
          )}
        </div>

        <div className="mt-5 flex items-center justify-between gap-3 text-sm text-slate-500">
          <button type="button" disabled={!paginacion.anterior || loading} onClick={() => setPage((currentPage) => Math.max(currentPage - 1, 1))} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:opacity-50">
            Anterior
          </button>
          <span className="rounded-2xl bg-slate-100 px-4 py-2 font-semibold text-slate-700">Página {paginacion.pagina} de {paginacion.paginas}</span>
          <button type="button" disabled={!paginacion.siguiente || loading} onClick={() => setPage((currentPage) => currentPage + 1)} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 disabled:opacity-50">
            Siguiente
          </button>
        </div>
      </section>
    </section>
  );
}

export default DocentesPage;