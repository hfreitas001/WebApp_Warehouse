import { useState, useEffect } from "react";
import { admin as adminApi } from "../api";
import { useAuth } from "../AuthContext";

const MODULE_IDS = [
  "inbound", "outbound", "adjustments", "lancamentos_manuais",
  "movimentacoes", "pedidos_abertos", "dashboard", "admin_usuarios",
];

export default function AdminUsuarios() {
  const { can } = useAuth();
  const [pending, setPending] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!can("admin_usuarios")) return;
    Promise.all([adminApi.pending(), adminApi.users()])
      .then(([p, u]) => {
        setPending(p || []);
        setUsers(u || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [can]);

  if (!can("admin_usuarios")) {
    return <div className="page"><p className="error">Sem permissão.</p></div>;
  }
  if (loading) return <div className="page"><div className="loading-wrap"><span className="loading-spinner" aria-hidden="true" />Carregando...</div></div>;
  if (error) return <div className="page"><p className="error">{error}</p></div>;

  const handleApprove = async (email) => {
    try {
      await adminApi.approve(email);
      setPending((p) => p.filter((r) => r.email !== email));
      setUsers((u) => u.map((r) => (r.email === email ? { ...r, approved_at: new Date().toISOString() } : r)));
    } catch (e) {
      alert(e.message);
    }
  };

  const handleSaveModules = async (email, allowed_modules) => {
    try {
      await adminApi.updateModules(email, allowed_modules);
      alert("Salvo.");
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Admin Usuários</h1>
      <h2 className="page-subtitle">Aguardando aprovação</h2>
      {pending.length === 0 ? (
        <p className="muted">Nenhum usuário aguardando aprovação.</p>
      ) : (
        <ul className="list">
          {pending.map((r) => (
            <li key={r.email} className="list-item">
              <span>{r.email}</span>
              <button type="button" className="btn small" onClick={() => handleApprove(r.email)}>Aprovar</button>
            </li>
          ))}
        </ul>
      )}
      <h2 className="page-subtitle">Todos os usuários</h2>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>E-mail</th>
              <th>Role</th>
              <th>Aprovado</th>
            </tr>
          </thead>
          <tbody>
            {users.map((r) => (
              <tr key={r.email}>
                <td>{r.email}</td>
                <td>{r.role}</td>
                <td>{r.approved_at ? "Sim" : "Não"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
