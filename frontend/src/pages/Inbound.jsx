import { useState, useEffect, useMemo } from "react";
import { data as dataApi, orders as ordersApi } from "../api";

const TIPO_COL = "transfer_type";
const ORDER_ID_COL = "order_id";
const ITEM_CODE_COL = "item_code";
const OPEN_QTY_COL = "open_quantity";

function useAddr() {
  const [addr, setAddr] = useState([]);
  useEffect(() => {
    dataApi.load().then((r) => {
      const list = (r?.addr || []).map((a) => a.Adress || a.address).filter(Boolean);
      setAddr([...new Set(list)]);
    }).catch(() => setAddr([]));
  }, []);
  return addr;
}

function useOpenOrders() {
  const [open, setOpen] = useState([]);
  const [fulfilled, setFulfilled] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setLoading(true);
    Promise.all([ordersApi.open(), ordersApi.fulfilled()])
      .then(([o, f]) => {
        setOpen(Array.isArray(o) ? o : []);
        setFulfilled(Array.isArray(f) ? f : []);
      })
      .catch(() => { setOpen([]); setFulfilled([]); })
      .finally(() => setLoading(false));
  }, []);
  return { open, fulfilled, loading };
}

function buildFulfilledMap(fulfilled) {
  const map = {};
  (fulfilled || []).forEach((r) => {
    const k = (r.order_id || "") + "|" + (r.item_code || "");
    map[k] = (map[k] || 0) + Number(r.quantity_fulfilled || 0);
  });
  return map;
}

export default function Inbound() {
  const enderecos = useAddr();
  const { open, fulfilled, loading: ordersLoading } = useOpenOrders();
  const [fluxo, setFluxo] = useState("bipagem");
  const [queue, setQueue] = useState([]);
  const [jsonInput, setJsonInput] = useState("");
  const [endereco, setEndereco] = useState("");
  const [sending, setSending] = useState(false);
  const [msg, setMsg] = useState(null);

  const addressOptions = enderecos.length ? enderecos : ["D1"];
  useEffect(() => {
    if (addressOptions[0] && !endereco) setEndereco(addressOptions[0]);
  }, [addressOptions, endereco]);

  const fulfilledMap = useMemo(() => buildFulfilledMap(fulfilled), [fulfilled]);
  const openWithPendente = useMemo(() => {
    const openCol = open[0]?.open_quantity != null ? OPEN_QTY_COL : "quantity";
    return (open || []).map((r) => {
      const k = (r[ORDER_ID_COL] || "") + "|" + (r[ITEM_CODE_COL] || "");
      const solicitado = Number(r[openCol] ?? r.quantity ?? 0) || 0;
      const atendido = fulfilledMap[k] || 0;
      const pendente = Math.max(0, solicitado - atendido);
      return { ...r, _solicitado: solicitado, atendido, pendente, [TIPO_COL]: r[TIPO_COL] ?? "—" };
    }).filter((r) => r.pendente > 0);
  }, [open, fulfilledMap]);

  const tipos = useMemo(() => {
    const set = new Set(openWithPendente.map((r) => String(r[TIPO_COL])));
    return [...set].sort();
  }, [openWithPendente]);
  const [tipoSel, setTipoSel] = useState("");
  const ordersByTipo = useMemo(() => {
    if (!tipoSel) return [];
    return openWithPendente.filter((r) => String(r[TIPO_COL]) === tipoSel);
  }, [openWithPendente, tipoSel]);
  const orderIds = useMemo(() => {
    const set = new Set(ordersByTipo.map((r) => r[ORDER_ID_COL]));
    return [...set].sort();
  }, [ordersByTipo]);
  const [orderSel, setOrderSel] = useState("");
  const linesInOrder = useMemo(() => {
    if (!orderSel) return [];
    return ordersByTipo.filter((r) => String(r[ORDER_ID_COL]) === orderSel);
  }, [ordersByTipo, orderSel]);
  const [lineIdx, setLineIdx] = useState(0);
  const selectedLine = linesInOrder[lineIdx] || null;
  const [qtyAtender, setQtyAtender] = useState(1);
  const [sendingAtender, setSendingAtender] = useState(false);
  const [msgAtender, setMsgAtender] = useState(null);

  useEffect(() => {
    if (tipos.length && !tipoSel) setTipoSel(tipos[0]);
  }, [tipos, tipoSel]);
  useEffect(() => {
    if (orderIds.length && !orderSel) setOrderSel(orderIds[0]);
  }, [orderIds, orderSel]);
  useEffect(() => {
    setLineIdx(0);
  }, [orderSel]);

  const addToQueue = () => {
    const raw = jsonInput.trim();
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      const arr = Array.isArray(parsed) ? parsed : [parsed];
      const itemCode = (arr[0]?.itemCode ?? arr[0]?.item_code)?.toString?.() ?? "";
      const qty = arr[0]?.quantity ?? arr[0]?.qty ?? 1;
      const batchId = arr[0]?.BatchId ?? arr[0]?.materialBatch ?? "N/A";
      const desc = arr[0]?.description ?? "Entrada WebApp";
      const expiry = arr[0]?.expiryDate ?? "N/A";
      setQueue((q) => [...q, { itemCode, quantity: qty, BatchId: batchId, description: desc, expiryDate: expiry }]);
      setJsonInput("");
      setMsg(null);
    } catch {
      setMsg({ type: "error", text: "JSON inválido." });
    }
  };

  const sendBatch = async () => {
    if (!queue.length) {
      setMsg({ type: "error", text: "Adicione itens à fila." });
      return;
    }
    if (!endereco) {
      setMsg({ type: "error", text: "Selecione o endereço." });
      return;
    }
    setSending(true);
    setMsg(null);
    try {
      await dataApi.inboundBatch({
        address: endereco,
        items: queue.map((i) => ({
          itemCode: i.itemCode,
          quantity: i.quantity,
          BatchId: i.BatchId,
          description: i.description,
          expiryDate: i.expiryDate,
        })),
      });
      setMsg({ type: "success", text: "Estoque atualizado." });
      setQueue([]);
    } catch (err) {
      setMsg({ type: "error", text: err?.message || "Erro ao enviar." });
    } finally {
      setSending(false);
    }
  };

  const sendAtenderPedido = async () => {
    if (!selectedLine || !endereco) return;
    const qty = Math.min(Number(qtyAtender) || 1, selectedLine.pendente);
    setSendingAtender(true);
    setMsgAtender(null);
    try {
      await dataApi.inboundBatch({
        address: endereco,
        order_id: selectedLine[ORDER_ID_COL],
        items: [{
          itemCode: selectedLine[ITEM_CODE_COL],
          quantity: qty,
          description: `Atendimento pedido ${selectedLine[ORDER_ID_COL]}`,
        }],
      });
      setMsgAtender({ type: "success", text: `Entrada registrada. Pendente restante: ${selectedLine.pendente - qty}` });
      setQtyAtender(1);
    } catch (err) {
      setMsgAtender({ type: "error", text: err?.message || "Erro ao registrar." });
    } finally {
      setSendingAtender(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Inbound – Bipagem contínua</h1>
      <p className="page-desc">Entrada de mercadorias por bipagem livre ou vinculada a pedido em aberto.</p>

      <div className="fluxo-tabs">
        <label className="fluxo-option">
          <input
            type="radio"
            name="fluxo"
            checked={fluxo === "bipagem"}
            onChange={() => setFluxo("bipagem")}
          />
          <span>Bipagem livre</span>
        </label>
        <label className="fluxo-option">
          <input
            type="radio"
            name="fluxo"
            checked={fluxo === "pedido"}
            onChange={() => setFluxo("pedido")}
          />
          <span>Atender pedido</span>
        </label>
      </div>

      {fluxo === "bipagem" && (
        <>
          <section className="panel">
            <h2 className="panel-title">Bipe o JSON</h2>
            <p className="muted" style={{ marginBottom: "0.75rem" }}>
              Cole o JSON do item (um objeto ou array) e clique em Adicionar à fila.
            </p>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              className="form-input"
              placeholder='{"itemCode":"SKU-001","quantity":10,"BatchId":"...","description":"..."}'
              rows={4}
              style={{ fontFamily: "monospace", fontSize: "0.8125rem" }}
            />
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
              <button type="button" className="btn primary" onClick={addToQueue}>
                Adicionar à fila
              </button>
            </div>
            {msg && <p className={msg.type === "error" ? "error" : "success"} style={{ marginTop: "0.5rem" }}>{msg.text}</p>}
          </section>

          {queue.length > 0 && (
            <section className="panel">
              <h2 className="panel-title">Fila ({queue.length} itens)</h2>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Quantidade</th>
                      <th>Lote</th>
                    </tr>
                  </thead>
                  <tbody>
                    {queue.map((item, i) => (
                      <tr key={i}>
                        <td>{item.itemCode}</td>
                        <td>{item.quantity}</td>
                        <td>{item.BatchId ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="form-row" style={{ marginTop: "1rem" }}>
                <label className="form-label">Endereço</label>
                <select
                  value={endereco}
                  onChange={(e) => setEndereco(e.target.value)}
                  className="form-input"
                  style={{ maxWidth: "240px" }}
                >
                  {addressOptions.map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                <button type="button" className="btn primary" onClick={sendBatch} disabled={sending}>
                  {sending ? "Enviando..." : "Enviar para BigQuery"}
                </button>
              </div>
            </section>
          )}
        </>
      )}

      {fluxo === "pedido" && (
        <section className="panel">
          <h2 className="panel-title">Atender pedido</h2>
          {ordersLoading && <p className="muted">Carregando pedidos...</p>}
          {!ordersLoading && openWithPendente.length === 0 && (
            <p className="muted">Nenhuma linha de pedido com quantidade pendente.</p>
          )}
          {!ordersLoading && openWithPendente.length > 0 && (
            <>
              <div className="form-row">
                <label className="form-label">Tipo</label>
                <select
                  value={tipoSel}
                  onChange={(e) => setTipoSel(e.target.value)}
                  className="form-input"
                  style={{ maxWidth: "200px" }}
                >
                  {tipos.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Pedido (order_id)</label>
                <select
                  value={orderSel}
                  onChange={(e) => setOrderSel(e.target.value)}
                  className="form-input"
                  style={{ maxWidth: "240px" }}
                >
                  {orderIds.map((id) => (
                    <option key={id} value={id}>{id}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Item (linha do pedido)</label>
                <select
                  value={lineIdx}
                  onChange={(e) => setLineIdx(Number(e.target.value))}
                  className="form-input"
                  style={{ maxWidth: "360px" }}
                >
                  {linesInOrder.map((row, i) => (
                    <option key={i} value={i}>
                      {row[ITEM_CODE_COL]} | solicitado: {row._solicitado} | atendido: {row.atendido} | pendente: {row.pendente}
                    </option>
                  ))}
                </select>
              </div>
              {selectedLine && (
                <>
                  <p className="muted" style={{ marginBottom: "0.5rem" }}>
                    Pedido <strong>{selectedLine[ORDER_ID_COL]}</strong> · Item <strong>{selectedLine[ITEM_CODE_COL]}</strong> · Pendente <strong>{selectedLine.pendente}</strong>
                  </p>
                  <div className="form-row">
                    <label className="form-label">Quantidade a dar entrada</label>
                    <input
                      type="number"
                      min={1}
                      max={selectedLine.pendente}
                      value={qtyAtender}
                      onChange={(e) => setQtyAtender(Number(e.target.value) || 1)}
                      className="form-input"
                      style={{ maxWidth: "120px" }}
                    />
                  </div>
                  <div className="form-row">
                    <label className="form-label">Endereço</label>
                    <select
                      value={endereco}
                      onChange={(e) => setEndereco(e.target.value)}
                      className="form-input"
                      style={{ maxWidth: "240px" }}
                    >
                      {addressOptions.map((a) => (
                        <option key={a} value={a}>{a}</option>
                      ))}
                    </select>
                  </div>
                  {msgAtender && (
                    <p className={msgAtender.type === "error" ? "error" : "success"} style={{ marginBottom: "0.5rem" }}>{msgAtender.text}</p>
                  )}
                  <button
                    type="button"
                    className="btn primary"
                    onClick={sendAtenderPedido}
                    disabled={sendingAtender}
                  >
                    {sendingAtender ? "Registrando..." : "Registrar entrada (atender pedido)"}
                  </button>
                </>
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
