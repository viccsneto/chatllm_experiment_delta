const { useEffect, useRef, useState } = React;

function Sidebar({ sessions, activeSessionId, onSelect, onNew, onDelete, onRename }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const editRef = useRef(null);

  useEffect(() => {
    if (editingId) {
      editRef.current?.focus();
      editRef.current?.select();
    }
  }, [editingId]);

  const handleDoubleClick = (session) => {
    setEditingId(session.id);
    setEditValue(session.title || "Nova conversa");
  };

  const handleRenameSubmit = (sessionId) => {
    const trimmed = editValue.trim();
    if (trimmed) {
      onRename(sessionId, trimmed);
    }
    setEditingId(null);
  };

  const handleKeyDown = (e, sessionId) => {
    if (e.key === "Enter") {
      handleRenameSubmit(sessionId);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-brand">ChatLLM Lab</span>
      </div>
      <button className="sidebar-new-btn" onClick={onNew}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <line x1="8" y1="2" x2="8" y2="14" />
          <line x1="2" y1="8" x2="14" y2="8" />
        </svg>
        Nova conversa
      </button>
      <div className="sidebar-list">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`sidebar-item ${session.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelect(session.id)}
          >
            {editingId === session.id ? (
              <input
                ref={editRef}
                className="sidebar-edit-input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={() => handleRenameSubmit(session.id)}
                onKeyDown={(e) => handleKeyDown(e, session.id)}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <span
                className="sidebar-item-title"
                onDoubleClick={(e) => { e.stopPropagation(); handleDoubleClick(session); }}
                title="Duplo clique para renomear"
              >
                {session.title || "Nova conversa"}
              </span>
            )}
            <button
              className="sidebar-item-delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(session.id);
              }}
              title="Excluir conversa"
              aria-label="Excluir conversa"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                <line x1="3" y1="3" x2="11" y2="11" />
                <line x1="11" y1="3" x2="3" y2="11" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}