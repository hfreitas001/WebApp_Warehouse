import { useState, useEffect } from "react";
import { data as dataApi } from "../api";

function useStock() {
  const [stock, setStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    dataApi
      .stock()
      .then(setStock)
      .catch((e) => setError(e?.message || "Erro ao carregar"))
      .finally(() => setLoading(false));
  }, []);
  return { stock, loading, error };
}

function BarChart({ data, valueKey = "value", labelKey = "label" }) {
  const max = Math.max(...data.map((d) => Number(d[valueKey]) || 0), 1);
  return (
    <div className="chart-bars" role="img" aria-label="Gráfico de barras">
      {data.map((d, i) => (
        <div key={i} className="chart-bar-row">
          <span className="chart-bar-label">{d[labelKey]}</span>
          <div className="chart-bar-track">
            <div
              className="chart-bar-fill"
              style={{ width: `${((Number(d[valueKey]) || 0) / max) * 100}%` }}
            />
          </div>
          <span className="chart-bar-value">{Number(d[valueKey]) || 0}</span>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { stock, loading, error } = useStock();

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
  if (error) {
    return (
      <div className="page">
        <p className="error">{error}</p>
      </div>
    );
  }

  const totalQty = stock.reduce((s, r) => s + (Number(r.quantity) || 0), 0);
  const byAddress = (stock || []).reduce((acc, r) => {
    const addr = r.address ?? r.Address ?? "—";
    const q = Number(r.quantity) || 0;
    acc[addr] = (acc[addr] || 0) + q;
    return acc;
  }, {});
  const chartData = Object.entries(byAddress)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 12);

  return (
    <div className="page">
      <h1 className="page-title">Dashboard de Operações</h1>
      <p className="page-desc">Visão geral do estoque e quantidades por endereço.</p>

      <div className="cards-row">
        <div className="card">
          <div className="card-label">Volumes em Estoque</div>
          <div className="card-value">{stock.length}</div>
        </div>
        <div className="card">
          <div className="card-label">Qtd Total Itens</div>
          <div className="card-value">{totalQty.toLocaleString("pt-BR")}</div>
        </div>
      </div>

      {chartData.length > 0 && (
        <section className="panel">
          <h2 className="panel-title">Quantidade por endereço</h2>
          <BarChart data={chartData} valueKey="value" labelKey="label" />
        </section>
      )}

      <section className="panel">
        <h2 className="panel-title">Estoque (amostra)</h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Endereço</th>
                <th>Item</th>
                <th>Quantidade</th>
                <th>Lote</th>
              </tr>
            </thead>
            <tbody>
              {(stock || []).slice(0, 100).map((r, i) => (
                <tr key={i}>
                  <td>{r.address ?? r.Address ?? "—"}</td>
                  <td>{r.itemCode ?? r.item_code ?? "—"}</td>
                  <td>{r.quantity ?? "—"}</td>
                  <td>{r.BatchId ?? r.batchId ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {stock.length > 100 && (
          <p className="muted">Exibindo 100 de {stock.length} registros.</p>
        )}
        {stock.length === 0 && <p className="muted">Nenhum dado em estoque.</p>}
      </section>
    </div>
  );
}
