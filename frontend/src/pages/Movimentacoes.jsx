import { useState, useEffect, useMemo } from "react";
import { movements as movementsApi } from "../api";

function downloadCSV(rows, filename = "movimentacoes.csv") {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const line = (r) => headers.map((h) => JSON.stringify(r[h] ?? "")).join(",");
  const csv = [headers.join(","), ...rows.map(line)].join("\r\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function Movimentacoes() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterTipo, setFilterTipo] = useState([]);
  const [filterSource, setFilterSource] = useState([]);
  const [filterItem, setFilterItem] = useState("");

  useEffect(() => {
    movementsApi
      .list()
      .then((r) => setList(Array.isArray(r) ? r : []))
      .catch((e) => setError(e?.message || "Erro ao carregar"))
      .finally(() => setLoading(false));
  }, []);

  const tipos = useMemo(() => {
    const set = new Set((list || []).map((r) => r.movement_type).filter(Boolean));
    return [...set].sort();
  }, [list]);
  const sources = useMemo(() => {
    const set = new Set((list || []).map((r) => r.source).filter(Boolean));
    return [...set].sort();
  }, [list]);

  const filtered = useMemo(() => {
    let out = list;
    if (filterTipo.length > 0 && list[0]?.movement_type != null) {
      out = out.filter((r) => filterTipo.includes(r.movement_type));
    }
    if (filterSource.length > 0 && list[0]?.source != null) {
      out = out.filter((r) => filterSource.includes(r.source));
    }
    if (filterItem.trim()) {
      const q = filterItem.trim().toLowerCase();
      out = out.filter((r) =>
        String(r.item_code || "").toLowerCase().includes(q)
      );
    }
    return out;
  }, [list, filterTipo, filterSource, filterItem]);

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

  return (
    <div className="page">
      <h1 className="page-title">Histórico de movimentações</h1>
      <p className="page-desc">
        Registro de entradas, saídas e movimentações (tabela operations_webapp_warehouse_movements).
      </p>

      {list.length === 0 ? (
        <p className="muted">Nenhuma movimentação registrada ainda.</p>
      ) : (
        <>
          <details className="expander">
            <summary className="expander-header">Filtrar</summary>
            <div className="expander-body">
              <div className="form-row">
                <label className="form-label">Tipo (movement_type)</label>
                <select
                  multiple
                  value={filterTipo}
                  onChange={(e) => {
                    const opts = [...e.target.selectedOptions].map((o) => o.value);
                    setFilterTipo(opts);
                  }}
                  className="form-input"
                  style={{ minHeight: "80px" }}
                >
                  {tipos.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                <small className="muted">Segure Ctrl para múltiplos.</small>
              </div>
              <div className="form-row">
                <label className="form-label">Origem (source)</label>
                <select
                  multiple
                  value={filterSource}
                  onChange={(e) => {
                    const opts = [...e.target.selectedOptions].map((o) => o.value);
                    setFilterSource(opts);
                  }}
                  className="form-input"
                  style={{ minHeight: "80px" }}
                >
                  {sources.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Item (item_code)</label>
                <input
                  type="text"
                  value={filterItem}
                  onChange={(e) => setFilterItem(e.target.value)}
                  className="form-input"
                  placeholder="Ex: SKU-001"
                />
              </div>
            </div>
          </details>

          <div className="cards-row" style={{ marginBottom: "1rem" }}>
            <div className="card">
              <div className="card-label">Registros (filtrado)</div>
              <div className="card-value">{filtered.length}</div>
            </div>
          </div>

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
                {filtered.map((r, i) => (
                  <tr key={i}>
                    <td>{r.movement_at ?? "—"}</td>
                    <td>{r.movement_type ?? "—"}</td>
                    <td>{r.item_code ?? "—"}</td>
                    <td>{r.quantity ?? "—"}</td>
                    <td>{r.from_address ?? "—"}</td>
                    <td>{r.to_address ?? "—"}</td>
                    <td>{r.source ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: "1rem" }}>
            <button
              type="button"
              className="btn-outline"
              onClick={() => downloadCSV(filtered)}
            >
              Exportar CSV
            </button>
          </div>
        </>
      )}
    </div>
  );
}
