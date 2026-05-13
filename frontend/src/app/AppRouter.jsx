import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/auth/ProtectedRoute";
import LoginPage from "../pages/auth/LoginPage";
import DashboardPage from "../pages/dashboard/DashboardPage";
import ChangePasswordPage from "../pages/auth/ChangePasswordPage";
import CourseDetailPage from "../pages/cursos/CourseDetailPage";
import CursosPage from "../pages/cursos/CursosPage";
import CalificacionesPage from "../pages/calificaciones/CalificacionesPage";
import DocentesPage from "../pages/docentes/DocentesPage";
import ReportesPage from "../pages/reportes/ReportesPage";
import GradosPage from "../pages/grados/GradosPage";
import EstudiantesPage from "../pages/estudiantes/EstudiantesPage";
import HorariosPage from "../pages/horarios/HorariosPage";
import EnrollmentPage from "../pages/inscripcion/EnrollmentPage";
import PanelAcademicoLayout from "../layouts/PanelAcademicoLayout";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={(
            <ProtectedRoute>
              <PanelAcademicoLayout />
            </ProtectedRoute>
          )}
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/cursos" element={<CursosPage />} />
          <Route path="/docentes" element={<DocentesPage />} />
          <Route path="/cursos/detalle" element={<CourseDetailPage />} />
          <Route path="/change-password" element={<ChangePasswordPage />} />
          <Route path="/inscripcion" element={<EnrollmentPage />} />
          <Route path="/calificaciones" element={<CalificacionesPage />} />
          <Route path="/reportes" element={<ReportesPage />} />
          <Route path="/grados" element={<GradosPage />} />
          <Route path="/estudiantes" element={<EstudiantesPage />} />
          <Route path="/horarios" element={<HorariosPage />} />
        </Route>
        <Route
          path="*"
          element={(
            <Navigate to="/dashboard" replace />
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
