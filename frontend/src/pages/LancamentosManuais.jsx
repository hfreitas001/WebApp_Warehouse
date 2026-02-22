import { useState, useEffect } from "react";
import { data as dataApi, movements as movementsApi } from "../api";

export default function LancamentosManuais() {
  const [storages, setStorages] = useState([]);
  const [tipo, setTipo] = useState("ENTRADA");
  const [item, setItem] = useState("");
  const [qty, setQty] = useState(1);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [desc, setDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    dataApi.storages().then(setStorages).catch(() => setStorages([]));
  }, []);

  const opts = [""].concat(storages);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!item.trim()) { setMessage({ type: "error", text: "Informe o item." }); return; }
    setSubmitting(true);
    setMessage(null);
    try {
      await movementsApi.log({
        movement_type: tipo,
        item_code: item.trim(),
        quantity: qty,
        from_address: from || null,
        to_address: to || null,
        description: (desc && desc.trim()) || "Lancamento manual " + tipo,
        source: "WEBAPP_LANCAMENTO_MANUAL",
      });
      setMessage({ type: "success", text: "Lancamento registrado." });
      setItem("");
      setDesc("");
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Lancamentos manuais</h1>
      <p className="muted">Registra uma linha no historico de movimentacoes (sem alterar estoque).</p>
      <form onSubmit={handleSubmit} className="form">
        <div className="form-row">
          <label className="form-label">Tipo</label>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="form-input">
            <option value="ENTRADA">ENTRADA</option>
            <option value="SAIDA">SAIDA</option>
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Item (SKU)</label>
          <input value={item} onChange={(e) => setItem(e.target.value)} className="form-input" placeholder="Ex: SKU-001" />
        </div>
        <div className="form-row">
          <label className="form-label">Quantidade</label>
          <input type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} className="form-input" />
        </div>
        <div className="form-row">
          <label className="form-label">Endereco origem</label>
          <select value={from} onChange={(e) => setFrom(e.target.value)} className="form-input">
            {opts.map((o) => <option key={o || "x"} value={o}>{o || "-"}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Endereco destino</label>
          <select value={to} onChange={(e) => setTo(e.target.value)} className="form-input">
            {opts.map((o) => <option key={o || "y"} value={o}>{o || "-"}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Descricao</label>
          <input value={desc} onChange={(e) => setDesc(e.target.value)} className="form-input" placeholder="Opcional" />
        </div>
        {message && <p className={message.type === "error" ? "error" : "success"}>{message.text}</p>}
        <button type="submit" className="btn primary" disabled={submitting}>{submitting ? "Registrando..." : "Registrar"}</button>
      </form>
    </div>
  );
}
