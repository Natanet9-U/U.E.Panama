import { NavLink, Outlet } from "react-router-dom";
import { getStoredUser } from "../services/authService";

const menu = [
  { to: "/dashboard", label: "Dashboard", icon: "home" },
  { to: "/estudiantes", label: "Estudiantes", icon: "users" },
  { to: "/cursos", label: "Cursos", icon: "book" },
  { to: "/reportes", label: "Reportes", icon: "report" },
  { to: "/horarios", label: "Horarios", icon: "calendar" },
  { to: "/calificaciones", label: "Calificaciones", icon: "grade" },
];

function Icon({ name, className = "w-5 h-5" }) {
  switch (name) {
    case "home":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 11.5L12 4l9 7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M5 21V12h14v9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "users":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "book":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 5.5A2.5 2.5 0 016.5 3H20v18H6.5A2.5 2.5 0 014 19.5V5.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "report":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 17v-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 17v-10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M15 17v-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      );
    case "calendar":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
          <path d="M16 3v4M8 3v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "grade":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2l3 6 6 .5-4.5 3.5L19 20l-7-4-7 4 1.5-7L2 8.5 8 8 12 2z" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return null;
  }
}

function PanelAcademicoLayout() {
  const usuario = getStoredUser();

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex min-h-screen">
        <aside className="hidden lg:flex lg:w-72 lg:flex-col lg:rounded-r-2xl lg:bg-white lg:shadow-md">
          <div className="flex h-full flex-col justify-between p-6">
            <div>
              <div className="mb-6 flex items-center gap-3">
                <div className="rounded-md bg-indigo-50 p-2">
                  <svg className="h-6 w-6 text-indigo-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 3L3 8v6c0 5 4 9 9 9s9-4 9-9V8l-9-5z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-slate-900">U.E.Panama</h1>
                  <p className="text-xs text-slate-400">Panel docente</p>
                </div>
              </div>

              <nav className="flex flex-col gap-2">
                {menu.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-700 hover:bg-slate-100"
                      }`
                    }
                  >
                    <div className="text-slate-400">
                      <Icon name={item.icon} className="w-5 h-5" />
                    </div>
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </nav>
            </div>

            <div className="mt-6 flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
              <img src="/assets/login/avatar.png" alt="avatar" className="h-10 w-10 rounded-full object-cover" />
              <div>
                <div className="text-sm font-semibold text-slate-900">{usuario ? `${usuario.nombre} ${usuario.apellido}` : "María Álvarez"}</div>
                <div className="text-xs text-slate-400">Docente</div>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex flex-1 flex-col">
          <header className="sticky top-0 z-20 flex items-center justify-between border-b bg-white px-6 py-3">
            <div className="flex items-center gap-4">
              <button className="lg:hidden rounded-md p-2 text-slate-600">☰</button>
              <h2 className="text-lg font-semibold text-slate-900">U.E.Panama</h2>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:block">
                <input placeholder="Buscar..." className="w-64 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm outline-none focus:ring-1 focus:ring-indigo-300" />
              </div>
              <button title="Notificaciones" className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h11z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <button title="Ajustes" className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 15.5A3.5 3.5 0 1112 8.5a3.5 3.5 0 010 7z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 005 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 5c.4-.24.84-.39 1.31-.44V3a2 2 0 014 0v.09c.47.05.91.2 1.31.44a1.65 1.65 0 001.82.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019 9c.24.4.39.84.44 1.31H21a2 2 0 010 4h-.09c-.05.47-.2.91-.44 1.31z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              <div className="flex items-center gap-3">
                <img src="/assets/login/avatar.png" alt="avatar" className="h-9 w-9 rounded-full object-cover" />
              </div>
            </div>
          </header>

          <main className="p-6">
            <div className="mx-auto max-w-7xl">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default PanelAcademicoLayout;
