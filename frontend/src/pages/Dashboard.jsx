import { useState, useEffect } from "react";
import { data as dataApi } from "../api";

export default function Dashboard() {
  const [stock, setStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    dataApi
      .stock()
      .then(setStock)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page">
        <div className="loading-wrap">
          <span className="loading-spinner" aria-hidden="true" />
          Carregando...
        </div>
      </div>
    );
  }
  if (error) return <div className="page"><p className="error">{error}</p></div>;

  const totalQty = stock.reduce((s, r) => s + (Number(r.quantity) || 0), 0);
  return (
    <div className="page">
      <h1 className="page-title">Visão geral</h1>
      <div className="cards-row">
        <div className="card">
          <div className="card-label">Volumes em estoque</div>
          <div className="card-value">{stock.length}</div>
        </div>
        <div className="card">
          <div className="card-label">Quantidade total</div>
          <div className="card-value">{totalQty}</div>
        </div>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Endereço</th>
              <th>Item</th>
              <th>Quantidade</th>
            </tr>
          </thead>
          <tbody>
            {stock.slice(0, 100).map((r, i) => (
              <tr key={i}>
                <td>{r.address ?? r.Address ?? "—"}</td>
                <td>{r.itemCode ?? r.item_code ?? "—"}</td>
                <td>{r.quantity ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {stock.length > 100 && <p className="muted">Exibindo 100 de {stock.length}</p>}
      </div>
    </div>
  );
}
