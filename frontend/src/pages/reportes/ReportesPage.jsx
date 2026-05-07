import { useEffect, useState } from "react";
import LineChartMock from "../../components/charts/LineChartMock";
import { getReportsPage } from "../../services/reportsService";

const EMPTY_ARRAY = [];

function StatCard({ item }) {
  const toneStyles = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-emerald-600 bg-emerald-50",
    violet: "text-violet-600 bg-violet-50",
    orange: "text-orange-600 bg-orange-50",
  };

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-500">{item.titulo}</h3>
          <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{item.valor}</p>
          <p className="mt-2 text-xs font-semibold text-emerald-600">{item.detalle}</p>
        </div>
        <div className={`rounded-2xl p-3 ${toneStyles[item.acento] || toneStyles.blue}`}>
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
      </div>
    </article>
  );
}

function DistributionCard({ title, items }) {
  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
      <h3 className="text-lg font-black text-slate-950">{title}</h3>
      <div className="mt-5 space-y-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-900">{item.label}</p>
                <p className="text-xs text-slate-500">{item.count} estudiantes</p>
              </div>
              <p className={`text-lg font-black ${item.color}`}>{item.percentage}%</p>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function AttendanceBar({ grade, percentage, count }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-900">{grade}</p>
        <p className="text-sm text-slate-600">{percentage}%</p>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div style={{ width: `${percentage}%` }} className="h-full bg-emerald-500" />
      </div>
      <p className="text-xs text-slate-500">{count} estudiantes</p>
    </div>
  );
}

function SubjectRank({ rank, name, average }) {
  return (
    <article className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">{rank}</div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{name}</p>
          <p className="text-xs text-slate-500">Promedio: {average}</p>
        </div>
      </div>
      <svg className="h-5 w-5 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    </article>
  );
}

function ReportFile({ title, category, date, size }) {
  const categoryStyles = {
    Académico: "bg-blue-50 text-blue-700",
    Asistencia: "bg-emerald-50 text-emerald-700",
    Evaluación: "bg-violet-50 text-violet-700",
    Estadísticas: "bg-orange-50 text-orange-700",
  };

  return (
    <article className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-4">
        <div className="rounded-2xl bg-slate-100 p-3">
          <svg className="h-6 w-6 text-slate-600" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <div className="mt-1 flex items-center gap-3">
            <span className={`rounded-full px-2 py-1 text-xs font-semibold ${categoryStyles[category] || categoryStyles.Académico}`}>{category}</span>
            <p className="text-xs text-slate-500">{date} · {size}</p>
          </div>
        </div>
      </div>
      <button type="button" className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
        Descargar
      </button>
    </article>
  );
}

function ReportesPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getReportsPage({})
      .then((response) => {
        if (!mounted) return;
        setData(response);
        setError("");
      })
      .catch((requestError) => {
        if (!mounted) return;
        setError(requestError?.response?.data?.error || "No fue posible cargar los reportes");
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

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(99,102,241,0.08),rgba(255,255,255,0.94),rgba(14,165,233,0.05))] p-8 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400">U.E.Panama</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">Reportes</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">Análisis y estadísticas del desempeño académico</p>
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <button type="button" className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              Todos los reportes
            </button>
            <button type="button" className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-200 transition hover:bg-slate-800">
              Generar Reporte
            </button>
          </div>
        </div>
      </header>

      {error ? <div className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">{error}</div> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-36 animate-pulse rounded-3xl bg-slate-200" />)
          : resumen.map((item) => <StatCard key={item.titulo} item={item} />)}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Tendencia de Rendimiento y Asistencia</h2>
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">Últimos 6 meses</span>
          </div>
          <div className="mt-6 h-80 rounded-3xl border border-slate-100 bg-slate-50 p-4">
            <LineChartMock 
              data={[90, 88, 92, 89, 91, 87]} 
              labels={["Ene", "Feb", "Mar", "Abr", "May", "Jun"]} 
              color="#3b82f6" 
            />
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-black text-slate-950">Crecimiento de Estudiantes</h2>
            <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">Por mes</span>
          </div>
          <div className="mt-6 h-80 rounded-3xl border border-slate-100 bg-slate-50 p-4">
            <LineChartMock 
              data={[280, 290, 305, 318, 330, 340]} 
              labels={["Ene", "Feb", "Mar", "Abr", "May", "Jun"]} 
              color="#8b5cf6" 
            />
          </div>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr_1fr]">
        <DistributionCard
          title="Rendimiento por Nivel"
          items={[
            { label: "Excelente (90-100)", count: 113, percentage: 35, color: "text-emerald-600" },
            { label: "Bueno (80-89)", count: 146, percentage: 45, color: "text-blue-600" },
            { label: "Regular (70-79)", count: 49, percentage: 15, color: "text-orange-600" },
            { label: "Deficiente (<70)", count: 16, percentage: 5, color: "text-red-600" },
          ]}
        />

        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h3 className="text-lg font-black text-slate-950">Asistencia por Grado</h3>
          <div className="mt-5 space-y-4">
            <AttendanceBar grade="10°A" percentage={95} count={82} />
            <AttendanceBar grade="10°B" percentage={93} count={78} />
            <AttendanceBar grade="11°A" percentage={91} count={85} />
            <AttendanceBar grade="11°B" percentage={89} count={79} />
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
          <h3 className="text-lg font-black text-slate-950">Top Asignaturas</h3>
          <div className="mt-5 space-y-3">
            <SubjectRank rank="1" name="Inglés" average="89.2" />
            <SubjectRank rank="2" name="Ciencias" average="88.5" />
            <SubjectRank rank="3" name="Matemáticas" average="87.8" />
            <SubjectRank rank="4" name="Lenguaje" average="87.8" />
            <SubjectRank rank="5" name="Historia" average="87.2" />
          </div>
        </article>
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
        <h2 className="text-xl font-black text-slate-950">Reportes Generados</h2>
        <div className="mt-6 space-y-3">
          <ReportFile 
            title="Reporte de Rendimiento Académico - Semestre 1" 
            category="Académico" 
            date="15 Jun 2024" 
            size="2.4 MB" 
          />
          <ReportFile 
            title="Análisis de Asistencia - Mayo 2024" 
            category="Asistencia" 
            date="1 Jun 2024" 
            size="1.8 MB" 
          />
          <ReportFile 
            title="Evaluación de Cursos - Trimestre 2" 
            category="Evaluación" 
            date="28 May 2024" 
            size="3.1 MB" 
          />
          <ReportFile 
            title="Estadísticas de Estudiantes - Anual" 
            category="Estadísticas" 
            date="15 May 2024" 
            size="4.2 MB" 
          />
        </div>
      </section>
    </section>
  );
}

export default ReportesPage;
