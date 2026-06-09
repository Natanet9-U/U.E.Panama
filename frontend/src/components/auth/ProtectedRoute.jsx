import { Navigate } from "react-router-dom";
import { getStoredUser, isAuthenticated } from "../../services/authService";

function ProtectedRoute({ children, allowedRoles = [] }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length) {
    const usuario = getStoredUser();
    const userRoles = new Set(
      [usuario?.cargo, usuario?.rol, ...(Array.isArray(usuario?.roles) ? usuario.roles : [])]
        .filter(Boolean)
        .map((role) => `${role}`.toLowerCase()),
    );

    const allowed = allowedRoles.some((role) => userRoles.has(`${role}`.toLowerCase()));
    if (!allowed) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}

export default ProtectedRoute;
