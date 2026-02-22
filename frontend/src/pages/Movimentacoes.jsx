import { useState, useEffect } from "react";
import { movements as movementsApi } from "../api";

export default function Movimentacoes() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    movementsApi.list().then(setList).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="loading-wrap"><span className="loading-spinner" aria-hidden="true" />Carregando...</div></div>;
  if (error) return <div className="page"><p className="error">{error}</p></div>;

  return (
    <div className="page">
      <h1 className="page-title">Movimentacoes</h1>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Tipo</th>
              <th>Item</th>
              <th>Qtd</th>
              <th>Origem</th>
              <th>Destino</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {list.map((r, i) => (
              <tr key={i}>
                <td>{r.movement_at}</td>
                <td>{r.movement_type}</td>
                <td>{r.item_code}</td>
                <td>{r.quantity}</td>
                <td>{r.from_address}</td>
                <td>{r.to_address}</td>
                <td>{r.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && <p className="muted">Nenhuma movimentacao.</p>}
      </div>
    </div>
  );
}
