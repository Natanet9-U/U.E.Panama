import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, getStoredUser, logout } from "../../services/authService";

function DashboardPage() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(getStoredUser());

  useEffect(() => {
    let mounted = true;

    getCurrentUser()
      .then((user) => {
        if (mounted) {
          setUsuario(user);
        }
      })
      .catch(() => {
        logout();
        navigate("/login", { replace: true });
      });

    return () => {
      mounted = false;
    };
  }, [navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <section className="mx-auto max-w-6xl bg-white rounded-2xl shadow-panel p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="m-0 text-3xl font-bold text-slate-800">Dashboard</h1>
            <p className="mt-2 mb-0 text-slate-600">Connect</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="px-4 py-2 rounded-lg bg-slate-800 text-white border-none cursor-pointer hover:bg-slate-700 transition"
          >
            Cerrar sesion
          </button>
        </div>

        <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="m-0 text-slate-700">
            Usuario: {usuario ? `${usuario.nombre} ${usuario.apellido}` : "Cargando..."}
          </p>
          <p className="m-0 mt-1 text-slate-600">Email: {usuario?.email || "-"}</p>
        </div>
      </section>
    </main>
  );
}

export default DashboardPage;
