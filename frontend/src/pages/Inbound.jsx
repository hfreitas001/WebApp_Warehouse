import { useState, useEffect } from "react";
import { data as dataApi } from "../api";

export default function Inbound() {
  const [addr, setAddr] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      if (cancelled) return;
      setLoading(false);
    }, 8000);
    dataApi
      .load()
      .then((r) => {
        if (cancelled) return;
        const list = (r && r.addr ? r.addr : []).map((a) => a.Adress || a.address).filter(Boolean);
        setAddr([...new Set(list)]);
        setError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e && e.message ? e.message : "Erro ao carregar");
      })
      .finally(() => {
        if (cancelled) return;
        clearTimeout(t);
        setLoading(false);
      });
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  const enderecos = addr.length ? addr : ["D1"];

  return (
    <div className="page">
      <h1 className="page-title">Inbound</h1>
      <p className="muted">Entrada de mercadorias. O fluxo completo (atender pedido, bipagem) está no app Streamlit.</p>
      {loading && !error && <p className="muted">Carregando endereços...</p>}
      {error && <p className="error">API indisponível ou erro: {error}. Verifique se a API está rodando (porta 8000).</p>}
      {!loading && <p className="muted">Endereços disponíveis: {enderecos.join(", ")}</p>}
    </div>
  );
}
