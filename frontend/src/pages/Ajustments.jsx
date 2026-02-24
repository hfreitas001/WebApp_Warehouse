import { useState, useEffect } from "react";
import { data as dataApi } from "../api";

export default function Ajustments() {
  const [storages, setStorages] = useState([]);
  const [stock, setStock] = useState([]);
  const [tab, setTab] = useState("entrada");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [entradaItem, setEntradaItem] = useState("");
  const [entradaQty, setEntradaQty] = useState(1);
  const [entradaLocal, setEntradaLocal] = useState("");
  const [entradaSubmitting, setEntradaSubmitting] = useState(false);
  const [entradaMsg, setEntradaMsg] = useState(null);

  const [saidaItem, setSaidaItem] = useState("");
  const [saidaQty, setSaidaQty] = useState(1);
  const [saidaLocal, setSaidaLocal] = useState("");
  const [saidaSubmitting, setSaidaSubmitting] = useState(false);
  const [saidaMsg, setSaidaMsg] = useState(null);

  useEffect(() => {
    dataApi.storages().then((s) => {
      setStorages(Array.isArray(s) ? s : []);
      if (Array.isArray(s) && s[0] && !entradaLocal) setEntradaLocal(s[0]);
      if (Array.isArray(s) && s[0] && !saidaLocal) setSaidaLocal(s[0]);
    }).catch(() => setStorages([]));
    dataApi.stock().then((st) => setStock(Array.isArray(st) ? st : [])).catch(() => setStock([]));
  }, []);

  useEffect(() => {
    if (storages.length && !entradaLocal) setEntradaLocal(storages[0]);
    if (storages.length && !saidaLocal) setSaidaLocal(storages[0]);
  }, [storages, entradaLocal, saidaLocal]);

  const loadStock = () => {
    setLoading(true);
    dataApi.stock().then((st) => setStock(Array.isArray(st) ? st : [])).catch(() => setStock([])).finally(() => setLoading(false));
  };

  const byStorage = (stock || []).reduce((acc, r) => {
    const addr = r.address ?? r.Address;
    if (!addr || !storages.includes(addr)) return acc;
    const key = addr;
    if (!acc[key]) acc[key] = [];
    acc[key].push(r);
    return acc;
  }, {});

  const handleEntrada = async (e) => {
    e.preventDefault();
    if (!entradaItem.trim()) {
      setEntradaMsg({ type: "error", text: "Informe o item code." });
      return;
    }
    setEntradaSubmitting(true);
    setEntradaMsg(null);
    try {
      await dataApi.depositoEntrada({
        item_code: entradaItem.trim(),
        quantity: entradaQty,
        address: entradaLocal,
      });
      setEntradaMsg({ type: "success", text: `Entrada registrada: ${entradaQty} un. de ${entradaItem.trim()} em ${entradaLocal}` });
      setEntradaItem("");
      setEntradaQty(1);
      loadStock();
    } catch (err) {
      setEntradaMsg({ type: "error", text: err?.message || "Erro ao registrar." });
    } finally {
      setEntradaSubmitting(false);
    }
  };

  const handleSaida = async (e) => {
    e.preventDefault();
    if (!saidaItem.trim()) {
      setSaidaMsg({ type: "error", text: "Informe o item code." });
      return;
    }
    setSaidaSubmitting(true);
    setSaidaMsg(null);
    try {
      await dataApi.depositoSaida({
        item_code: saidaItem.trim(),
        quantity: saidaQty,
        address: saidaLocal,
      });
      setSaidaMsg({ type: "success", text: `Saída registrada: ${saidaQty} un. de ${saidaItem.trim()} em ${saidaLocal}` });
      setSaidaItem("");
      setSaidaQty(1);
      loadStock();
    } catch (err) {
      setSaidaMsg({ type: "error", text: err?.message || "Erro ao registrar." });
    } finally {
      setSaidaSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Depósitos – Controle manual</h1>
      <p className="page-desc">
        Storage Andar 2 e Andar 3: entrada e saída manual por item, quantidade e local.
      </p>

      <div className="tabs">
        <button
          type="button"
          className={`tab ${tab === "entrada" ? "active" : ""}`}
          onClick={() => setTab("entrada")}
        >
          Entrada manual
        </button>
        <button
          type="button"
          className={`tab ${tab === "saida" ? "active" : ""}`}
          onClick={() => setTab("saida")}
        >
          Saída manual
        </button>
      </div>

      {tab === "entrada" && (
        <section className="panel">
          <form onSubmit={handleEntrada} className="form">
            <div className="form-row">
              <label className="form-label">Item code</label>
              <input
                value={entradaItem}
                onChange={(e) => setEntradaItem(e.target.value)}
                className="form-input"
                placeholder="Ex: SKU-001"
              />
            </div>
            <div className="form-row">
              <label className="form-label">Quantidade</label>
              <input
                type="number"
                min={1}
                value={entradaQty}
                onChange={(e) => setEntradaQty(Number(e.target.value) || 1)}
                className="form-input"
              />
            </div>
            <div className="form-row">
              <label className="form-label">Local (depósito)</label>
              <select
                value={entradaLocal}
                onChange={(e) => setEntradaLocal(e.target.value)}
                className="form-input"
              >
                {storages.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            {entradaMsg && (
              <p className={entradaMsg.type === "error" ? "error" : "success"} style={{ marginBottom: "0.5rem" }}>
                {entradaMsg.text}
              </p>
            )}
            <button type="submit" className="btn primary" disabled={entradaSubmitting}>
              {entradaSubmitting ? "Registrando..." : "Registrar entrada"}
            </button>
          </form>
        </section>
      )}

      {tab === "saida" && (
        <section className="panel">
          <form onSubmit={handleSaida} className="form">
            <div className="form-row">
              <label className="form-label">Item code</label>
              <input
                value={saidaItem}
                onChange={(e) => setSaidaItem(e.target.value)}
                className="form-input"
                placeholder="Ex: SKU-001"
              />
            </div>
            <div className="form-row">
              <label className="form-label">Quantidade</label>
              <input
                type="number"
                min={1}
                value={saidaQty}
                onChange={(e) => setSaidaQty(Number(e.target.value) || 1)}
                className="form-input"
              />
            </div>
            <div className="form-row">
              <label className="form-label">Local (depósito)</label>
              <select
                value={saidaLocal}
                onChange={(e) => setSaidaLocal(e.target.value)}
                className="form-input"
              >
                {storages.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            {saidaMsg && (
              <p className={saidaMsg.type === "error" ? "error" : "success"} style={{ marginBottom: "0.5rem" }}>
                {saidaMsg.text}
              </p>
            )}
            <button type="submit" className="btn primary" disabled={saidaSubmitting}>
              {saidaSubmitting ? "Registrando..." : "Registrar saída"}
            </button>
          </form>
        </section>
      )}

      <section className="panel">
        <h2 className="panel-title">Estoque por depósito</h2>
        <button type="button" className="btn-outline" onClick={loadStock} disabled={loading} style={{ marginBottom: "1rem" }}>
          {loading ? "Atualizando..." : "Atualizar"}
        </button>
        {storages.length === 0 && <p className="muted">Nenhum depósito configurado.</p>}
        {storages.length > 0 && Object.keys(byStorage).length === 0 && !loading && (
          <p className="muted">Nenhum registro nos depósitos Storage Andar 2/3.</p>
        )}
        {storages.map((storage) => {
          const rows = byStorage[storage] || [];
          const resumo = rows.reduce((acc, r) => {
            const code = r.itemCode ?? r.item_code ?? "—";
            const q = Number(r.quantity) || 0;
            acc[code] = (acc[code] || 0) + q;
            return acc;
          }, {});
          const resumoList = Object.entries(resumo).map(([itemCode, quantity]) => ({ address: storage, itemCode, quantity }));
          return (
            <div key={storage} style={{ marginBottom: "1rem" }}>
              <p className="muted" style={{ marginBottom: "0.35rem" }}><strong>{storage}</strong></p>
              {resumoList.length === 0 ? (
                <p className="muted">Vazio</p>
              ) : (
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
                      {resumoList.map((r, i) => (
                        <tr key={i}>
                          <td>{r.address}</td>
                          <td>{r.itemCode}</td>
                          <td>{r.quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
