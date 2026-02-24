import { useState, useEffect } from "react";
import { data as dataApi, movements as movementsApi } from "../api";

export default function LancamentosManuais() {
  const [storages, setStorages] = useState([]);
  const [tipo, setTipo] = useState("ENTRADA");
  const [item, setItem] = useState("");
  const [qty, setQty] = useState(1);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [orderId, setOrderId] = useState("");
  const [desc, setDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    dataApi.storages().then(setStorages).catch(() => setStorages([]));
  }, []);

  const opts = [""].concat(Array.isArray(storages) ? storages : []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!item.trim()) {
      setMessage({ type: "error", text: "Informe o item (SKU)." });
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      await movementsApi.log({
        movement_type: tipo,
        item_code: item.trim(),
        quantity: qty,
        from_address: from || null,
        to_address: to || null,
        order_id: orderId.trim() || null,
        description: (desc && desc.trim()) || `Lançamento manual ${tipo}`,
        source: "WEBAPP_LANCAMENTO_MANUAL",
      });
      setMessage({ type: "success", text: "Lançamento registrado no histórico de movimentações." });
      setItem("");
      setDesc("");
    } catch (err) {
      setMessage({ type: "error", text: err?.message || "Erro ao registrar." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Lançamentos manuais</h1>
      <p className="page-desc">
        Registra uma linha no histórico de movimentações (sem alterar estoque). Use para correções ou documentação.
      </p>

      <form onSubmit={handleSubmit} className="form form-grid">
        <div className="form-row">
          <label className="form-label">Tipo</label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className="form-input"
          >
            <option value="ENTRADA">ENTRADA</option>
            <option value="SAIDA">SAIDA</option>
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Item (SKU)</label>
          <input
            value={item}
            onChange={(e) => setItem(e.target.value)}
            className="form-input"
            placeholder="Ex: SKU-001"
          />
        </div>
        <div className="form-row">
          <label className="form-label">Quantidade</label>
          <input
            type="number"
            min={1}
            value={qty}
            onChange={(e) => setQty(Number(e.target.value) || 1)}
            className="form-input"
          />
        </div>
        <div className="form-row">
          <label className="form-label">Endereço origem</label>
          <select
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="form-input"
          >
            {opts.map((o) => (
              <option key={o || "x"} value={o}>{o || "—"}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Endereço destino</label>
          <select
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="form-input"
          >
            {opts.map((o) => (
              <option key={o || "y"} value={o}>{o || "—"}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Order ID (opcional)</label>
          <input
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            className="form-input"
            placeholder="Ex: ORD-123"
          />
        </div>
        <div className="form-row form-row-full">
          <label className="form-label">Descrição</label>
          <input
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="form-input"
            placeholder="Ex: Ajuste manual / Correção"
          />
        </div>
        {message && (
          <p className={message.type === "error" ? "error" : "success"} style={{ marginBottom: "0.5rem" }}>
            {message.text}
          </p>
        )}
        <div className="form-row form-row-full">
          <button type="submit" className="btn primary" disabled={submitting}>
            {submitting ? "Registrando..." : "Registrar lançamento"}
          </button>
        </div>
      </form>
    </div>
  );
}
