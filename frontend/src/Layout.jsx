import { useState, useCallback } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

const MODULES = [
  { id: "inbound", label: "Inbound", path: "/inbound" },
  { id: "outbound", label: "Outbound", path: "/outbound" },
  { id: "adjustments", label: "Ajustments", path: "/ajustments" },
  { id: "lancamentos_manuais", label: "Lancamentos manuais", path: "/lancamentos" },
];
const REPORTS = [
  { id: "movimentacoes", label: "Movimentacoes", path: "/movimentacoes" },
  { id: "pedidos_abertos", label: "Pedidos em aberto", path: "/pedidos" },
];
const DASH = { id: "dashboard", label: "Visao geral", path: "/" };
const CONFIG = [{ id: "admin_usuarios", label: "Admin Usuarios", path: "/admin" }];

const ICONS = {
  modules: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
  reports: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  config: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  chevron: (
    <svg className="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  inbound: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="7.5 4.21 12 6.81 16.5 4.21" />
      <line x1="12" y1="22" x2="12" y2="6" />
    </svg>
  ),
  outbound: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="16.5 19.79 12 17.19 7.5 19.79" />
      <line x1="12" y1="2" x2="12" y2="18" />
    </svg>
  ),
  adjustments: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="17" y1="16" x2="23" y2="16" />
    </svg>
  ),
  lancamentos: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  movimentacoes: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  pedidos: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
      <line x1="9" y1="14" x2="15" y2="14" />
      <line x1="9" y1="18" x2="15" y2="18" />
    </svg>
  ),
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  box: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
};

const linkIcon = (id) => {
  const map = {
    inbound: ICONS.inbound,
    outbound: ICONS.outbound,
    adjustments: ICONS.adjustments,
    lancamentos_manuais: ICONS.lancamentos,
    movimentacoes: ICONS.movimentacoes,
    pedidos_abertos: ICONS.pedidos,
    admin_usuarios: ICONS.admin,
  };
  return map[id] ?? ICONS.box;
};

function Section({ title, sectionKey, icon, items, open, onToggle, currentPath, onNavigate }) {
  return (
    <div className={`sidebar-section ${open ? "open" : ""}`}>
      <button type="button" className="sidebar-section-title" onClick={onToggle} aria-expanded={open}>
        {icon}
        {title}
        {ICONS.chevron}
      </button>
      {open && (
        <nav className="sidebar-links" aria-label={title}>
          {items.map((m) => (
            <Link
              key={m.id}
              to={m.path}
              className={currentPath === m.path ? "sidebar-link active" : "sidebar-link"}
              onClick={onNavigate}
            >
              {linkIcon(m.id)}
              {m.label}
            </Link>
          ))}
        </nav>
      )}
    </div>
  );
}

export default function Layout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [openSection, setOpenSection] = useState("modulos");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const mods = MODULES.filter((m) => can(m.id));
  const reps = REPORTS.filter((m) => can(m.id));
  const dash = can(DASH.id) ? DASH : null;
  const cfg = CONFIG.filter((m) => can(m.id));

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);
  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="layout">
      <div
        className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`}
        onClick={closeSidebar}
        aria-hidden="true"
      />
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`} aria-label="Navegacao">
        <div className="sidebar-accent" aria-hidden="true" />
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon" aria-hidden="true">
              {ICONS.box}
            </div>
            <span className="sidebar-title">WMS Tractian</span>
          </div>
          <button
            type="button"
            className="sidebar-close"
            onClick={closeSidebar}
            aria-label="Fechar menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        {user && (
          <>
            <div className="sidebar-user-block">
              <div className="sidebar-user-row">
                <div className="sidebar-user-avatar" aria-hidden="true">
                  {(user.email || "U").charAt(0).toUpperCase()}
                </div>
                <span className="sidebar-user-email">{user.email}</span>
              </div>
            </div>
            <button type="button" className="sidebar-logout" onClick={handleLogout}>
              {ICONS.logout}
              Sair
            </button>
          </>
        )}
        <hr className="sidebar-hr" />
        <div className="sidebar-nav">
          {mods.length > 0 && (
            <Section
              title="Modulos"
              sectionKey="modulos"
              icon={ICONS.modules}
              items={mods}
              open={openSection === "modulos"}
              onToggle={() => setOpenSection(openSection === "modulos" ? "" : "modulos")}
              currentPath={location.pathname}
              onNavigate={closeSidebar}
            />
          )}
          {reps.length > 0 && (
            <Section
              title="Relatorios"
              sectionKey="relatorios"
              icon={ICONS.reports}
              items={reps}
              open={openSection === "relatorios"}
              onToggle={() => setOpenSection(openSection === "relatorios" ? "" : "relatorios")}
              currentPath={location.pathname}
              onNavigate={closeSidebar}
            />
          )}
          {dash && (
            <div className="sidebar-section">
              <Link
                to={dash.path}
                className={location.pathname === "/" ? "sidebar-dash-link active" : "sidebar-dash-link"}
                onClick={closeSidebar}
              >
                {ICONS.dashboard}
                {dash.label}
              </Link>
            </div>
          )}
          {cfg.length > 0 && (
            <Section
              title="Configuracoes"
              sectionKey="config"
              icon={ICONS.config}
              items={cfg}
              open={openSection === "config"}
              onToggle={() => setOpenSection(openSection === "config" ? "" : "config")}
              currentPath={location.pathname}
              onNavigate={closeSidebar}
            />
          )}
        </div>
      </aside>

      <header className="main-header">
        <button
          type="button"
          className="main-header-menu"
          onClick={() => setSidebarOpen(true)}
          aria-label="Abrir menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        <span className="main-header-title">WMS Tractian</span>
      </header>

      <main className="main" id="main-content">
        <div className="main-inner">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
