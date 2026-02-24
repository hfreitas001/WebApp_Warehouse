import { useState, useEffect, useMemo } from "react";
import { data as dataApi, orders as ordersApi } from "../api";

const TIPO_COL = "transfer_type";
const ORDER_ID_COL = "order_id";
const ITEM_CODE_COL = "item_code";
const OPEN_QTY_COL = "open_quantity";

function parseBatchDate(batchId) {
  if (!batchId || typeof batchId !== "string") return "99991231";
  const m = batchId.slice(0, 8).match(/^\d{8}$/);
  return m ? batchId.slice(0, 8) : "99991231";
}

/** Plano FEFO: caixas inteiras (cada linha = 1 BoxId, DELETE no BQ). */
function buildPickList(stock, itemCode, qtyNeeded) {
  const rows = (stock || []).filter((r) => String(r.itemCode ?? r.item_code ?? "").trim() === String(itemCode).trim());
  if (rows.length === 0) return [];
  const withDate = rows.map((r) => ({ ...r, _sort: parseBatchDate(r.BatchId ?? r.batchId) }));
  withDate.sort((a, b) => a._sort.localeCompare(b._sort));
  let need = Number(qtyNeeded) || 0;
  const pick = [];
  for (const r of withDate) {
    if (need <= 0) break;
    const q = Number(r.quantity) || 0;
    if (q <= 0) continue;
    pick.push({
      boxId: r.BoxId ?? r.boxId,
      itemCode: r.itemCode ?? r.item_code,
      quantity: q,
      from_address: r.address ?? r.Address,
    });
    need -= q;
  }
  return pick;
}

function useStock() {
  const [stock, setStock] = useState([]);
  useEffect(() => {
    dataApi.stock().then((s) => setStock(Array.isArray(s) ? s : [])).catch(() => setStock([]));
  }, []);
  return stock;
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

export default function Outbound() {
  const stock = useStock();
  const { open, fulfilled, loading: ordersLoading } = useOpenOrders();
  const [fluxo, setFluxo] = useState("livre");
  const [pickList, setPickList] = useState([]);
  const [pickOrderId, setPickOrderId] = useState(null);

  const [itemLivre, setItemLivre] = useState("");
  const [qtyLivre, setQtyLivre] = useState(1);
  const [confirming, setConfirming] = useState(false);
  const [msg, setMsg] = useState(null);

  const skus = useMemo(() => {
    const set = new Set((stock || []).map((r) => r.itemCode ?? r.item_code).filter(Boolean));
    return [...set].sort();
  }, [stock]);

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
  const orderIds = useMemo(() => [...new Set(ordersByTipo.map((r) => r[ORDER_ID_COL]))].sort(), [ordersByTipo]);
  const [orderSel, setOrderSel] = useState("");
  const linesInOrder = useMemo(() => {
    if (!orderSel) return [];
    return ordersByTipo.filter((r) => String(r[ORDER_ID_COL]) === orderSel);
  }, [ordersByTipo, orderSel]);
  const [lineIdx, setLineIdx] = useState(0);
  const selectedLine = linesInOrder[lineIdx] || null;
  const disponivel = useMemo(() => {
    if (!selectedLine) return 0;
    const itemCode = selectedLine[ITEM_CODE_COL];
    return (stock || []).reduce((s, r) => {
      if (String(r.itemCode ?? r.item_code) !== String(itemCode)) return s;
      return s + (Number(r.quantity) || 0);
    }, 0);
  }, [stock, selectedLine]);
  const qtyMaxAtender = selectedLine ? Math.min(selectedLine.pendente, Math.floor(disponivel)) : 0;
  const [qtyAtender, setQtyAtender] = useState(1);

  useEffect(() => {
    if (skus.length && !itemLivre) setItemLivre(skus[0]);
  }, [skus, itemLivre]);
  useEffect(() => {
    if (tipos.length && !tipoSel) setTipoSel(tipos[0]);
  }, [tipos, tipoSel]);
  useEffect(() => {
    if (orderIds.length && !orderSel) setOrderSel(orderIds[0]);
  }, [orderIds, orderSel]);
  useEffect(() => {
    setLineIdx(0);
  }, [orderSel]);
  useEffect(() => {
    if (selectedLine && qtyMaxAtender > 0) setQtyAtender(Math.min(qtyAtender, qtyMaxAtender));
  }, [selectedLine, qtyMaxAtender]);

  const gerarPlanoLivre = () => {
    if (!itemLivre) return;
    const pick = buildPickList(stock, itemLivre, qtyLivre);
    setPickList(pick);
    setPickOrderId(null);
    setMsg(null);
  };

  const gerarPlanoAtender = () => {
    if (!selectedLine || qtyMaxAtender <= 0) return;
    const qty = Math.min(Number(qtyAtender) || 1, qtyMaxAtender);
    const pick = buildPickList(stock, selectedLine[ITEM_CODE_COL], qty);
    setPickList(pick);
    setPickOrderId(selectedLine[ORDER_ID_COL]);
    setMsg(null);
  };

  const confirmarSaida = async () => {
    if (!pickList.length) return;
    setConfirming(true);
    setMsg(null);
    try {
      await dataApi.outboundConfirm({
        order_id: pickOrderId || undefined,
        picks: pickList.map((p) => ({
          boxId: p.boxId,
          itemCode: p.itemCode,
          quantity: p.quantity,
          from_address: p.from_address,
        })),
      });
      setMsg({ type: "success", text: "Baixa realizada!" });
      setPickList([]);
      setPickOrderId(null);
    } catch (err) {
      setMsg({ type: "error", text: err?.message || "Erro ao confirmar." });
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Outbound – Saída</h1>
      <p className="page-desc">Picking livre ou vinculado a pedido em aberto (FEFO).</p>

      <div className="fluxo-tabs">
        <label className="fluxo-option">
          <input
            type="radio"
            name="fluxo_out"
            checked={fluxo === "livre"}
            onChange={() => setFluxo("livre")}
          />
          <span>Picking livre</span>
        </label>
        <label className="fluxo-option">
          <input
            type="radio"
            name="fluxo_out"
            checked={fluxo === "pedido"}
            onChange={() => setFluxo("pedido")}
          />
          <span>Atender pedido</span>
        </label>
      </div>

      {fluxo === "livre" && (
        <section className="panel">
          <h2 className="panel-title">Gerar plano de picking</h2>
          {stock.length === 0 ? (
            <p className="muted">Estoque vazio.</p>
          ) : (
            <>
              <div className="form-row">
                <label className="form-label">SKU</label>
                <select
                  value={itemLivre}
                  onChange={(e) => setItemLivre(e.target.value)}
                  className="form-input"
                  style={{ maxWidth: "200px" }}
                >
                  {skus.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Qtd</label>
                <input
                  type="number"
                  min={1}
                  value={qtyLivre}
                  onChange={(e) => setQtyLivre(Number(e.target.value) || 1)}
                  className="form-input"
                  style={{ maxWidth: "100px" }}
                />
              </div>
              <button type="button" className="btn primary" onClick={gerarPlanoLivre}>
                Gerar plano
              </button>
            </>
          )}
        </section>
      )}

      {fluxo === "pedido" && (
        <section className="panel">
          <h2 className="panel-title">Atender pedido</h2>
          {ordersLoading && <p className="muted">Carregando...</p>}
          {!ordersLoading && openWithPendente.length === 0 && (
            <p className="muted">Nenhuma linha com quantidade pendente.</p>
          )}
          {!ordersLoading && openWithPendente.length > 0 && (
            <>
              <div className="form-row">
                <label className="form-label">Tipo</label>
                <select value={tipoSel} onChange={(e) => setTipoSel(e.target.value)} className="form-input" style={{ maxWidth: "200px" }}>
                  {tipos.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Pedido (order_id)</label>
                <select value={orderSel} onChange={(e) => setOrderSel(e.target.value)} className="form-input" style={{ maxWidth: "240px" }}>
                  {orderIds.map((id) => <option key={id} value={id}>{id}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Item (linha)</label>
                <select value={lineIdx} onChange={(e) => setLineIdx(Number(e.target.value))} className="form-input" style={{ maxWidth: "360px" }}>
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
                    Pedido <strong>{selectedLine[ORDER_ID_COL]}</strong> · Item <strong>{selectedLine[ITEM_CODE_COL]}</strong> · Pendente <strong>{selectedLine.pendente}</strong> · Disponível <strong>{disponivel}</strong>
                  </p>
                  {qtyMaxAtender <= 0 && (
                    <p className="error">Sem estoque suficiente para o item {selectedLine[ITEM_CODE_COL]}.</p>
                  )}
                  {qtyMaxAtender > 0 && (
                    <>
                      <div className="form-row">
                        <label className="form-label">Quantidade a dar saída</label>
                        <input
                          type="number"
                          min={1}
                          max={qtyMaxAtender}
                          value={qtyAtender}
                          onChange={(e) => setQtyAtender(Number(e.target.value) || 1)}
                          className="form-input"
                          style={{ maxWidth: "120px" }}
                        />
                      </div>
                      <button type="button" className="btn primary" onClick={gerarPlanoAtender}>
                        Gerar plano de picking
                      </button>
                    </>
                  )}
                </>
              )}
            </>
          )}
        </section>
      )}

      {pickList.length > 0 && (
        <section className="panel">
          <h2 className="panel-title">Plano de picking</h2>
          {pickOrderId && <p className="muted" style={{ marginBottom: "0.5rem" }}>Pedido: <strong>{pickOrderId}</strong></p>}
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>BoxId</th>
                  <th>Item</th>
                  <th>Qtd</th>
                  <th>Endereço</th>
                </tr>
              </thead>
              <tbody>
                {pickList.map((p, i) => (
                  <tr key={i}>
                    <td>{p.boxId}</td>
                    <td>{p.itemCode}</td>
                    <td>{p.quantity}</td>
                    <td>{p.from_address ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {msg && <p className={msg.type === "error" ? "error" : "success"} style={{ marginBottom: "0.5rem" }}>{msg.text}</p>}
          <button type="button" className="btn primary" onClick={confirmarSaida} disabled={confirming}>
            {confirming ? "Confirmando..." : "Confirmar saída"}
          </button>
        </section>
      )}
    </div>
  );
}
