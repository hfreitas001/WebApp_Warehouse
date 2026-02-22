import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Layout from "./Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Inbound from "./pages/Inbound";
import Outbound from "./pages/Outbound";
import Ajustments from "./pages/Ajustments";
import LancamentosManuais from "./pages/LancamentosManuais";
import Movimentacoes from "./pages/Movimentacoes";
import PedidosAbertos from "./pages/PedidosAbertos";
import AdminUsuarios from "./pages/AdminUsuarios";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="loading-wrap">
        <span className="loading-spinner" aria-hidden="true" />
        Carregando...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="inbound" element={<Inbound />} />
        <Route path="outbound" element={<Outbound />} />
        <Route path="ajustments" element={<Ajustments />} />
        <Route path="lancamentos" element={<LancamentosManuais />} />
        <Route path="movimentacoes" element={<Movimentacoes />} />
        <Route path="pedidos" element={<PedidosAbertos />} />
        <Route path="admin" element={<AdminUsuarios />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
