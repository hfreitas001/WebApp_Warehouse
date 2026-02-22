import { useState, useEffect } from "react";
import { orders as ordersApi } from "../api";

export default function PedidosAbertos() {
  const [open, setOpen] = useState([]);
  const [fulfilled, setFulfilled] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    Promise.all([ordersApi.open(), ordersApi.fulfilled()]).then(([o, f]) => { setOpen(o || []); setFulfilled(f || []); }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);
  const fulfilledMap = {};
  (fulfilled || []).forEach((r) => {
    const k = (r.order_id || "") + "|" + (r.item_code || "");
    fulfilledMap[k] = (fulfilledMap[k] || 0) + Number(r.quantity_fulfilled || 0);
  });
  if (loading) return <div className="page"><div className="loading-wrap"><span className="loading-spinner" aria-hidden="true" />Carregando...</div></div>;
  if (error) return <div className="page"><p className="error">{error}</p></div>;
  return (
    <div className="page">
      <h1 className="page-title">Pedidos em aberto</h1>
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>order_id</th><th>item_code</th><th>open_quantity</th><th>Atendido</th></tr></thead>
          <tbody>
            {(open || []).slice(0, 200).map((r, i) => {
              const k = (r.order_id || "") + "|" + (r.item_code || "");
              return <tr key={i}><td>{r.order_id}</td><td>{r.item_code}</td><td>{r.open_quantity != null ? r.open_quantity : r.quantity}</td><td>{fulfilledMap[k] || 0}</td></tr>;
            })}
          </tbody>
        </table>
        {(open || []).length === 0 && <p className="muted">Nenhum pedido em aberto.</p>}
      </div>
    </div>
  );
}
