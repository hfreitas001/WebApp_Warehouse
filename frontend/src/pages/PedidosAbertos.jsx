import { useState, useEffect, useMemo } from "react";
import { orders as ordersApi } from "../api";

const TIPO_COL = "transfer_type";
const ORDER_ID_COL = "order_id";
const ITEM_CODE_COL = "item_code";
const OPEN_QTY_COL = "open_quantity";
const QTY_COL = "quantity";

function useOrders() {
  const [open, setOpen] = useState([]);
  const [fulfilled, setFulfilled] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    Promise.all([ordersApi.open(), ordersApi.fulfilled()])
      .then(([o, f]) => {
        setOpen(Array.isArray(o) ? o : []);
        setFulfilled(Array.isArray(f) ? f : []);
      })
      .catch((e) => setError(e?.message || "Erro ao carregar"))
      .finally(() => setLoading(false));
  }, []);
  return { open, fulfilled, loading, error };
}

function buildFulfilledMap(fulfilled) {
  const map = {};
  (fulfilled || []).forEach((r) => {
    const k = (r.order_id || "") + "|" + (r.item_code || "");
    map[k] = (map[k] || 0) + Number(r.quantity_fulfilled || 0);
  });
  return map;
}

function enrichWithPendente(openList, fulfilledMap) {
  const openCol = openList[0] && (openList[0].open_quantity != null || openList[0].quantity != null)
    ? (openList[0].open_quantity != null ? OPEN_QTY_COL : QTY_COL)
    : OPEN_QTY_COL;
  return (openList || []).map((r) => {
    const k = (r.order_id || "") + "|" + (r.item_code || "");
    const solicitado = Number(r[openCol] ?? r.quantity ?? r.open_quantity ?? 0) || 0;
    const atendido = fulfilledMap[k] || 0;
    const pendente = Math.max(0, solicitado - atendido);
    return {
      ...r,
      _solicitado: solicitado,
      atendido,
      pendente,
      [TIPO_COL]: r[TIPO_COL] ?? "—",
    };
  });
}

function downloadCSV(rows, filename) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]).filter((k) => !k.startsWith("_"));
  const line = (r) => headers.map((h) => JSON.stringify(r[h] ?? "")).join(",");
  const csv = [headers.join(","), ...rows.map(line)].join("\r\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function BarChart({ data, valueKey, labelKey }) {
  const max = Math.max(...data.map((d) => Number(d[valueKey]) || 0), 1);
  return (
    <div className="chart-bars" role="img" aria-label="Pedidos por tipo">
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

export default function PedidosAbertos() {
  const { open, fulfilled, loading, error } = useOrders();
  const [tipoFilter, setTipoFilter] = useState("Todos");

  const fulfilledMap = useMemo(() => buildFulfilledMap(fulfilled), [fulfilled]);
  const enriched = useMemo(
    () => enrichWithPendente(open, fulfilledMap),
    [open, fulfilledMap]
  );

  const tipos = useMemo(() => {
    const set = new Set(enriched.map((r) => String(r[TIPO_COL] ?? "—")));
    return ["Todos", ...[...set].sort()];
  }, [enriched]);

  const filtered = useMemo(() => {
    if (tipoFilter === "Todos") return enriched;
    return enriched.filter((r) => String(r[TIPO_COL]) === tipoFilter);
  }, [enriched, tipoFilter]);

  const countByType = useMemo(() => {
    const byType = {};
    enriched.forEach((r) => {
      const t = String(r[TIPO_COL] ?? "—");
      byType[t] = byType[t] || { linhas: 0, pedidos: new Set() };
      byType[t].linhas += 1;
      byType[t].pedidos.add(r[ORDER_ID_COL]);
    });
    return Object.entries(byType).map(([tipo, v]) => ({
      tipo,
      linhas: v.linhas,
      pedidos_unicos: v.pedidos.size,
    })).sort((a, b) => b.pedidos_unicos - a.pedidos_unicos);
  }, [enriched]);

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
      <h1 className="page-title">Pedidos de transferência em aberto</h1>
      <p className="page-desc">
        Dados da fct_open_transfer_request_lines. Atendido/pendente a partir dos movimentos.
      </p>

      {open.length === 0 ? (
        <p className="muted">Nenhum pedido em aberto.</p>
      ) : (
        <>
          <section className="panel">
            <h2 className="panel-title">Dashboard de pedidos</h2>
            <div className="cards-row">
              {countByType.slice(0, 5).map((row, idx) => (
                <div key={idx} className="card">
                  <div className="card-label">{row.tipo}</div>
                  <div className="card-value">{row.pedidos_unicos}</div>
                  <span className="muted" style={{ fontSize: "0.75rem" }}>
                    {row.linhas} linhas
                  </span>
                </div>
              ))}
            </div>
            {countByType.length > 0 && (
              <BarChart
                data={countByType}
                valueKey="pedidos_unicos"
                labelKey="tipo"
              />
            )}
          </section>

          <section className="panel">
            <h2 className="panel-title">Filtrar por tipo</h2>
            <div className="form-row">
              <label className="form-label">Transfer type</label>
              <select
                value={tipoFilter}
                onChange={(e) => setTipoFilter(e.target.value)}
                className="form-input"
                style={{ maxWidth: "280px" }}
              >
                {tipos.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <p className="muted">Linhas em aberto (filtrado): <strong>{filtered.length}</strong></p>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>order_id</th>
                    <th>item_code</th>
                    <th>transfer_type</th>
                    <th>Solicitado</th>
                    <th>Atendido</th>
                    <th>Pendente</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r, i) => (
                    <tr key={i}>
                      <td>{r.order_id ?? "—"}</td>
                      <td>{r.item_code ?? "—"}</td>
                      <td>{r[TIPO_COL] ?? "—"}</td>
                      <td>{r._solicitado ?? "—"}</td>
                      <td>{r.atendido ?? "—"}</td>
                      <td>{r.pendente ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: "1rem" }}>
              <button
                type="button"
                className="btn-outline"
                onClick={() => downloadCSV(filtered, tipoFilter === "Todos" ? "pedidos_todos.csv" : `pedidos_${tipoFilter.replace(/\s/g, "_")}.csv`)}
              >
                Exportar CSV
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
