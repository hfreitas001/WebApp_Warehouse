import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth as authApi } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login(email.trim(), password);
      login(res.access_token, res.user);
      if (!res.user.approved_at) {
        setError("Conta aguardando aprovação do administrador.");
        return;
      }
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message || "Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">WMS Tractian</h1>
        <p className="login-subtitle">Entre com seu e-mail e senha</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label className="login-label">E-mail</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="login-input"
            required
            autoComplete="email"
          />
          <label className="login-label">Senha</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="login-input"
            required
            autoComplete="current-password"
          />
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
