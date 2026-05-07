const grados = [
  { grado: "7mo", estudiantes: 95, promedio: 84.2 },
  { grado: "8vo", estudiantes: 87, promedio: 82.9 },
  { grado: "9no", estudiantes: 92, promedio: 85.7 },
  { grado: "10mo", estudiantes: 78, promedio: 88.1 },
  { grado: "11mo", estudiantes: 64, promedio: 86.4 },
];

function GradosPage() {
  return (
    <section>
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900">Grados</h1>
        <p className="mt-1 text-slate-600">Resumen de rendimiento por nivel escolar.</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {grados.map((item) => (
          <article key={item.grado} className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-cyan-50 p-5">
            <p className="text-sm font-medium text-slate-500">{item.grado}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{item.estudiantes} estudiantes</p>
            <p className="mt-2 text-sm text-slate-700">Promedio general: {item.promedio}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default GradosPage;
