const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AppAuthenticated({ token, email, onLogout }) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const loadSessions = async () => {
    try {
      setLoadingSessions(true);
      const list = await fetchSessions();
      setSessions(list);
      if (list.length > 0 && !currentSessionId) {
        setCurrentSessionId(list[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSessions(false);
    }
  };

  const switchSession = useCallback(async (sessionId) => {
    if (busy) return;
    setCurrentSessionId(sessionId);
    try {
      const msgs = await fetchSessionMessages(sessionId);
      setMessages(
        msgs.length > 0
          ? msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
          : [{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]
      );
    } catch (e) {
      console.error(e);
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
    }
  }, [busy]);

  const handleNewSession = async () => {
    if (busy) return;
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
      setError("");
    } catch (e) {
      setError("Erro ao criar sessao.");
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (busy) return;
    try {
      await deleteSession(sessionId);
      const updated = sessions.filter((s) => s.id !== sessionId);
      setSessions(updated);
      if (currentSessionId === sessionId) {
        if (updated.length > 0) {
          switchSession(updated[0].id);
        } else {
          const session = await createSession();
          setSessions([session]);
          setCurrentSessionId(session.id);
          setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
        }
      }
    } catch (e) {
      setError("Erro ao deletar sessao.");
    }
  };

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    setError("");

    // Ensure we have a session
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        sessionId = session.id;
        setCurrentSessionId(session.id);
      } catch (e) {
        setError("Erro ao criar sessao.");
        return;
      }
    }

    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantMessageId, role: "assistant", content: "" },
    ]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        sessionId,
        history: chatHistory,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            )
          );
        },
      });

      // Reload sessions to get updated title
      const list = await fetchSessions();
      setSessions(list);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );
    } catch (err) {
      const aborted = err?.name === "AbortError";
      if (!aborted) {
        setError(err.message || "Falha inesperada ao gerar resposta.");
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content.trim() ? msg.content : "Nao foi possivel obter resposta do modelo agora." }
              : msg
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId && !msg.content.trim()
              ? { ...msg, content: "Resposta interrompida." }
              : msg
          )
        );
      }
    } finally {
      abortControllerRef.current = null;
      setBusy(false);
    }
  };

  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const title = currentSession?.title || "ChatLLM Lab";

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={handleNewSession} disabled={busy}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 2a.75.75 0 0 1 .75.75v4.5h4.5a.75.75 0 0 1 0 1.5h-4.5v4.5a.75.75 0 0 1-1.5 0v-4.5h-4.5a.75.75 0 0 1 0-1.5h4.5v-4.5A.75.75 0 0 1 8 2z"/>
            </svg>
            Nova conversa
          </button>
        </div>
        <div className="sidebar-list">
          {loadingSessions ? (
            <div className="sidebar-loading">Carregando...</div>
          ) : sessions.length === 0 ? (
            <div className="sidebar-empty">Nenhuma conversa</div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`sidebar-item ${session.id === currentSessionId ? "active" : ""}`}
                onClick={() => switchSession(session.id)}
              >
                <svg className="sidebar-item-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                  <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.71 1.7l.75.75a.75.75 0 0 1-.53 1.28H4.5a2.5 2.5 0 0 1-2.5-2.5zm10.5 5.5V1.5h-8a1 1 0 0 0-1 1v6.708A2.5 2.5 0 0 1 4.5 9h8z"/>
                </svg>
                <span className="sidebar-item-title">{session.title}</span>
                <button
                  className="sidebar-item-delete"
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  title="Deletar conversa"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <path d="M5.75 2h4.5a.75.75 0 0 1 .75.75V3.5h-6v-.75A.75.75 0 0 1 5.75 2zM4 3.5V2.75A2.25 2.25 0 0 1 6.25.5h3.5A2.25 2.25 0 0 1 12 2.75V3.5h2.25a.75.75 0 0 1 0 1.5h-.75v7.5A2.75 2.75 0 0 1 10.75 15h-5.5A2.75 2.75 0 0 1 2.5 12.25V4.75h-.75a.75.75 0 0 1 0-1.5H4zm1 3.25a.75.75 0 0 1 1.5 0v5a.75.75 0 0 1-1.5 0v-5zm4.5 0a.75.75 0 0 1 1.5 0v5a.75.75 0 0 1-1.5 0v-5z"/>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="sidebar-email">{email}</span>
            <button className="logout-btn" onClick={onLogout} title="Sair">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M4 4a3 3 0 0 1 3-3h2a3 3 0 0 1 3 3v.75a.75.75 0 0 1-1.5 0V4a1.5 1.5 0 0 0-1.5-1.5H7A1.5 1.5 0 0 0 5.5 4v8A1.5 1.5 0 0 0 7 13.5h2a1.5 1.5 0 0 0 1.5-1.5v-.75a.75.75 0 0 1 1.5 0v.75a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V4zm8.03 1.47a.75.75 0 0 1 1.06 0l2.5 2.5a.75.75 0 0 1 0 1.06l-2.5 2.5a.75.75 0 1 1-1.06-1.06l1.22-1.22H6.75a.75.75 0 0 1 0-1.5h6.5l-1.22-1.22a.75.75 0 0 1 0-1.06z"/>
              </svg>
              Sair
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-content">
        <header className="app-header">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M3 4a1 1 0 0 1 1-1h12a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1zm0 6a1 1 0 0 1 1-1h12a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1zm0 6a1 1 0 0 1 1-1h12a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1z"/>
            </svg>
          </button>
          <div className="brand">{title}</div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.map((msg) => (
              <article key={msg.id} className={`bubble ${msg.role}`}>
                <MessageContent content={msg.content} />
              </article>
            ))}
          </div>
        </section>

        <Composer
          text={text}
          busy={busy}
          error={error}
          onChangeText={setText}
          onSubmit={onSubmit}
          onStop={onStop}
        />

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </div>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [email, setEmail] = useState(() => localStorage.getItem("auth_email") || "");

  const handleLogin = (newToken, newEmail) => {
    setToken(newToken);
    setEmail(newEmail);
  };

  const handleLogout = () => {
    fetch(`${window.location.origin}/api/auth/logout`, { method: "POST" }).catch(() => {});
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_email");
    setToken(null);
    setEmail("");
  };

  if (!token) {
    return React.createElement(LoginPage, { onLogin: handleLogin });
  }

  return React.createElement(AppAuthenticated, { token, email, onLogout: handleLogout });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

