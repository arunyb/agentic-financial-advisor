import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppShell } from "./components/AppShell";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import PortfolioPage from "./pages/PortfolioPage";
import RiskProfilePage from "./pages/RiskProfilePage";
import AdvisorChat from "./pages/AdvisorChat";

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <Protected>
                <Dashboard />
              </Protected>
            }
          />
          <Route
            path="/portfolio"
            element={
              <Protected>
                <PortfolioPage />
              </Protected>
            }
          />
          <Route
            path="/risk"
            element={
              <Protected>
                <RiskProfilePage />
              </Protected>
            }
          />
          <Route
            path="/advisor"
            element={
              <Protected>
                <AdvisorChat />
              </Protected>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
