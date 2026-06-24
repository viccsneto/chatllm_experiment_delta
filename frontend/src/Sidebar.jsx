const { useState } = React;

function Sidebar({ sessions, activeSessionId, onSelectSession, onCreateSession, onDeleteSession, onRenameSession }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <button
          className="sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expandir sidebar" : "Recolher sidebar"}
        >
          {collapsed ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          )}
        </button>
        {!collapsed && <span className="sidebar-title">Sessoes</span>}
      </div>

      {!collapsed && (
        <>
          <button className="sidebar-new-btn" onClick={onCreateSession}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Nova sessao
          </button>

          <nav className="sidebar-list">
            {sessions.length === 0 && (
              <span className="sidebar-empty">Nenhuma sessao ainda</span>
            )}
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="sidebar-item-title" title={s.title || "Nova sessao"}>
                  {s.title || "Nova sessao"}
                </span>
                <button
                  className="sidebar-item-del"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  aria-label={`Excluir sessao ${s.id}`}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
          </nav>
        </>
      )}
    </aside>
  );
}
