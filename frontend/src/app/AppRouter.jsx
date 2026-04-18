import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/auth/ProtectedRoute";
import LoginPage from "../pages/auth/LoginPage";
import DashboardPage from "../pages/dashboard/DashboardPage";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={(
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
