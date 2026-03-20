import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppLayout } from "./components/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InsightsPage } from "./pages/InsightsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/feedback" element={<FeedbackPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/insights" element={<InsightsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/feedback" />} />
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            fontFamily: "Outfit, sans-serif",
            fontSize: "14px",
          },
        }}
      />
    </AuthProvider>
  );
}
