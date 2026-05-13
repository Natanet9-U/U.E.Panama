import { useEffect, useState } from "react";
import { searchExistingStudent, enrollNewStudent, reEnrollStudent, getEnrollmentCatalogs } from "../../services/enrollmentService";

const EMPTY_ARRAY = [];

function SearchStudentCard({ estudiante, onSelect }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-semibold">
              {estudiante.nombre.split(' ').map(n=>n[0]).slice(0,2).join('')}
            </div>
            <div>
              <p className="font-semibold text-slate-900">{estudiante.nombre}</p>
              <p className="text-xs text-slate-500">CI: {estudiante.ci}</p>
            </div>
          </div>
          <p className="text-sm text-slate-600 mt-2">
            Grado actual: <span className="font-semibold">{estudiante.grado_actual_nombre || "No asignado"}</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Estado: {estudiante.activo ? <span className="text-green-600 font-semibold">Activo</span> : <span className="text-yellow-600 font-semibold">Inactivo (disponible para reinscripción)</span>}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onSelect(estudiante)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white hover:bg-blue-700"
        >
          Seleccionar
        </button>
      </div>
    </div>
  );
}

function EnrollmentPage() {
  const [tab, setTab] = useState("search"); // "search" or "new"
  const [catalogs, setCatalogs] = useState({ grados: EMPTY_ARRAY, tutores: EMPTY_ARRAY });
  const [error, setError] = useState("");

  // Search Tab State
  const [searchCI, setSearchCI] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [foundStudent, setFoundStudent] = useState(null);
  const [selectedGradoForReEnroll, setSelectedGradoForReEnroll] = useState("");
  const [reEnrolling, setReEnrolling] = useState(false);

  // New Enrollment Tab State
  const [newForm, setNewForm] = useState({
    nombres: "",
    primer_apellido: "",
    segundo_apellido: "",
    ci: "",
    fecha_nacimiento: "",
    genero: "",
    grado_id: "",
    tutor_id: "",
  });
  const [newLoading, setNewLoading] = useState(false);
  const [newError, setNewError] = useState("");
  const [newSuccess, setNewSuccess] = useState("");

  useEffect(() => {
    let mounted = true;

    getEnrollmentCatalogs()
      .then((response) => {
        if (!mounted) return;
        setCatalogs(response);
        setError("");
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.response?.data?.error || "No fue posible cargar los catálogos");
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleSearchChange = (e) => {
    setSearchCI(e.target.value);
    setFoundStudent(null);
    setSearchError("");
  };

  const handleSearchStudent = async () => {
    if (!searchCI.trim()) {
      setSearchError("Debes ingresar un CI");
      return;
    }

    setSearchLoading(true);
    setSearchError("");
    setFoundStudent(null);

    try {
      const resultado = await searchExistingStudent(searchCI.trim());
      if (resultado.encontrado) {
        setFoundStudent(resultado.estudiante);
        setSelectedGradoForReEnroll("");
      } else {
        setSearchError("No se encontró estudiante con ese CI. Usa la sección de Inscripción Nueva.");
      }
    } catch (err) {
      setSearchError(err?.response?.data?.error || "Error al buscar estudiante");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleReEnroll = async () => {
    if (!foundStudent || !selectedGradoForReEnroll) {
      setSearchError("Debes seleccionar un grado");
      return;
    }

    setReEnrolling(true);
    setSearchError("");

    try {
      const resultado = await reEnrollStudent(foundStudent.ci, selectedGradoForReEnroll);
      setFoundStudent(null);
      setSearchCI("");
      setSelectedGradoForReEnroll("");
      alert(`✅ ${resultado.mensaje}`);
    } catch (err) {
      setSearchError(err?.response?.data?.error || "Error al reinscribir");
    } finally {
      setReEnrolling(false);
    }
  };

  const handleNewFormChange = (e) => {
    const { name, value } = e.target;
    setNewForm((current) => ({ ...current, [name]: value }));
    setNewError("");
  };

  const handleEnrollNew = async (e) => {
    e.preventDefault();
    if (!newForm.nombres || !newForm.primer_apellido || !newForm.ci || !newForm.grado_id) {
      setNewError("Debes llenar: nombres, primer apellido, CI y grado");
      return;
    }

    setNewLoading(true);
    setNewError("");
    setNewSuccess("");

    try {
      const resultado = await enrollNewStudent(newForm);
      setNewSuccess(resultado.mensaje);
      setNewForm({
        nombres: "",
        primer_apellido: "",
        segundo_apellido: "",
        ci: "",
        fecha_nacimiento: "",
        genero: "",
        grado_id: "",
        tutor_id: "",
      });
      setTimeout(() => setNewSuccess(""), 5000);
    } catch (err) {
      setNewError(err?.response?.data?.error || "Error al inscribir estudiante");
    } finally {
      setNewLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Inscripción de Estudiantes</h1>
          <p className="mt-2 max-w-2xl text-base text-slate-600">
            Gestiona la inscripción y reinscripción de estudiantes. El sistema detecta automáticamente si el estudiante ya fue inscrito anteriormente.
          </p>
        </div>
      </header>

      {error && <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div>}

      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <div className="flex gap-4 border-b border-slate-100">
          <button
            type="button"
            onClick={() => {
              setTab("search");
              setSearchError("");
            }}
            className={`px-4 py-3 font-semibold transition ${
              tab === "search"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            🔍 Reinscripción
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("new");
              setNewError("");
            }}
            className={`px-4 py-3 font-semibold transition ${
              tab === "new"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            ➕ Inscripción Nueva
          </button>
        </div>

        {/* Search/Re-enroll Tab */}
        {tab === "search" && (
          <div className="mt-6 space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Buscar Estudiante por CI
              </label>
              <p className="text-xs text-slate-500 mb-3">
                Si el estudiante ya fue inscrito anteriormente (y está inactivo), puedes reinscribirlo aquí.
              </p>
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Ingresa el CI del estudiante"
                  value={searchCI}
                  onChange={handleSearchChange}
                  className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
                <button
                  type="button"
                  onClick={handleSearchStudent}
                  disabled={searchLoading}
                  className="rounded-2xl bg-blue-600 px-6 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {searchLoading ? "Buscando..." : "Buscar"}
                </button>
              </div>
            </div>

            {searchError && (
              <div className="rounded-2xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800">
                {searchError}
              </div>
            )}

            {foundStudent && (
              <div className="space-y-4 p-4 rounded-2xl border border-blue-200 bg-blue-50">
                <SearchStudentCard
                  estudiante={foundStudent}
                  onSelect={() => {}}
                />

                {!foundStudent.activo && (
                  <div className="space-y-3">
                    <label className="block text-sm font-semibold text-slate-700">
                      Selecciona el nuevo grado para reinscripción:
                    </label>
                    <select
                      value={selectedGradoForReEnroll}
                      onChange={(e) => setSelectedGradoForReEnroll(e.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none"
                    >
                      <option value="">Selecciona un grado...</option>
                      {catalogs.grados.map((g) => (
                        <option key={g.id} value={g.id}>
                          {g.nombre}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleReEnroll}
                      disabled={reEnrolling || !selectedGradoForReEnroll}
                      className="w-full rounded-2xl bg-green-600 px-4 py-3 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {reEnrolling ? "Reinscribiendo..." : "✅ Reinscribir"}
                    </button>
                  </div>
                )}

                {foundStudent.activo && (
                  <div className="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
                    ⚠️ Este estudiante ya está activo en el sistema. No necesita reinscripción.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* New Enrollment Tab */}
        {tab === "new" && (
          <form onSubmit={handleEnrollNew} className="mt-6 space-y-6">
            {newSuccess && (
              <div className="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
                ✅ {newSuccess}
              </div>
            )}

            {newError && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {newError}
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Nombres *
                </label>
                <input
                  type="text"
                  name="nombres"
                  placeholder="Ej: Juan Pablo"
                  value={newForm.nombres}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Primer Apellido *
                </label>
                <input
                  type="text"
                  name="primer_apellido"
                  placeholder="Ej: García"
                  value={newForm.primer_apellido}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Segundo Apellido
                </label>
                <input
                  type="text"
                  name="segundo_apellido"
                  placeholder="Ej: López"
                  value={newForm.segundo_apellido}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  CI (Cédula) *
                </label>
                <input
                  type="text"
                  name="ci"
                  placeholder="Ej: 8-123-456"
                  value={newForm.ci}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Fecha de Nacimiento
                </label>
                <input
                  type="date"
                  name="fecha_nacimiento"
                  value={newForm.fecha_nacimiento}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Género
                </label>
                <select
                  name="genero"
                  value={newForm.genero}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                >
                  <option value="">Selecciona...</option>
                  <option value="M">Masculino</option>
                  <option value="F">Femenino</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Grado *
                </label>
                <select
                  name="grado_id"
                  value={newForm.grado_id}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                >
                  <option value="">Selecciona un grado...</option>
                  {catalogs.grados.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Tutor
                </label>
                <select
                  name="tutor_id"
                  value={newForm.tutor_id}
                  onChange={handleNewFormChange}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-300"
                >
                  <option value="">Sin asignar</option>
                  {catalogs.tutores.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-3 border-t border-slate-100 pt-6">
              <button
                type="submit"
                disabled={newLoading}
                className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {newLoading ? "Inscribiendo..." : "✅ Inscribir Estudiante"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setNewForm({
                    nombres: "",
                    primer_apellido: "",
                    segundo_apellido: "",
                    ci: "",
                    fecha_nacimiento: "",
                    genero: "",
                    grado_id: "",
                    tutor_id: "",
                  });
                  setNewError("");
                }}
                className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-900 hover:bg-slate-50"
              >
                Limpiar
              </button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}

export default EnrollmentPage;
