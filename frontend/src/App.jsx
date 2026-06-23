const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

const WELCOME_MESSAGE = {
  id: createMessageId(),
  role: "assistant",
  content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
};

function App() {
  const [authenticated, setAuthenticated] = useState(!!localStorage.getItem("auth_token"));
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const loadedSessionRef = useRef(null);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  const handleAuthSuccess = useCallback(() => {
    setAuthenticated(true);
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await logoutUser();
    } catch {
      // Ignore errors on logout
    }
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_email");
    localStorage.removeItem("auth_user_id");
    setAuthenticated(false);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([WELCOME_MESSAGE]);
  }, []);

  // Load sessions on mount
  useEffect(() => {
    if (!authenticated) return;
    fetchSessions()
      .then((list) => {
        setSessions(list);
        if (list.length > 0) {
          setActiveSessionId(list[0].id);
          loadMessages(list[0].id);
        }
      })
      .catch(() => {});
  }, [authenticated]);

  const loadMessages = useCallback(async (sessionId) => {
    try {
      const msgs = await fetchSessionMessages(sessionId);
      if (msgs.length === 0) {
        setMessages([WELCOME_MESSAGE]);
      } else {
        setMessages(
          msgs.map((m) => ({
            id: createMessageId(),
            role: m.role,
            content: m.content,
          }))
        );
      }
      loadedSessionRef.current = sessionId;
    } catch {
      setMessages([WELCOME_MESSAGE]);
    }
  }, []);

  // Switch session
  const switchSession = useCallback(
    (sessionId) => {
      if (busy) abortControllerRef.current?.abort();
      setActiveSessionId(sessionId);
      setError("");
      loadMessages(sessionId);
    },
    [busy, loadMessages]
  );

  const handleNewSession = useCallback(async () => {
    if (busy) abortControllerRef.current?.abort();
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([WELCOME_MESSAGE]);
      setError("");
      loadedSessionRef.current = session.id;
    } catch (err) {
      setError(err.message);
    }
  }, [busy]);

  const handleDeleteSession = useCallback(
    async (sessionId, event) => {
      event.stopPropagation();
      if (busy) abortControllerRef.current?.abort();
      try {
        await deleteSession(sessionId);
        const updated = sessions.filter((s) => s.id !== sessionId);
        setSessions(updated);
        if (activeSessionId === sessionId) {
          if (updated.length > 0) {
            setActiveSessionId(updated[0].id);
            loadMessages(updated[0].id);
          } else {
            setActiveSessionId(null);
            setMessages([WELCOME_MESSAGE]);
          }
        }
      } catch (err) {
        setError(err.message);
      }
    },
    [sessions, activeSessionId, busy, loadMessages]
  );

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

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

    // Ensure there is an active session
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        setActiveSessionId(session.id);
        currentSessionId = session.id;
        loadedSessionRef.current = session.id;
      } catch (err) {
        setError(err.message);
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

    // Callback for session info from stream completion
    const onDelta = (delta) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `${msg.content}${delta}` }
            : msg
        )
      );
    };
    onDelta.__sessionCallback = (sessionId, title) => {
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title } : s))
      );
    };

    try {
      await sendMessageStream({
        message: cleaned,
        sessionId: currentSessionId,
        history: chatHistory,
        signal: abortController.signal,
        onDelta,
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

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  // If not authenticated, show login screen
  if (!authenticated) {
    return <Login onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <button className="sidebar-new-btn" onClick={handleNewSession} title="Nova conversa">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="8" y1="2" x2="8" y2="14" />
              <line x1="2" y1="8" x2="14" y2="8" />
            </svg>
            Nova conversa
          </button>
        </div>
        <nav className="sidebar-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar-item ${s.id === activeSessionId ? "active" : ""}`}
              onClick={() => switchSession(s.id)}
            >
              <span className="sidebar-item-title">{s.title}</span>
              <button
                className="sidebar-del-btn"
                onClick={(e) => handleDeleteSession(s.id, e)}
                title="Deletar sessao"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <line x1="2" y1="2" x2="10" y2="10" />
                  <line x1="10" y1="2" x2="2" y2="10" />
                </svg>
              </button>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="sidebar-email">{localStorage.getItem("auth_email")}</span>
          <button className="sidebar-logout-btn" onClick={handleLogout} title="Sair">
            Sair
          </button>
        </div>
      </aside>

      {/* Main area */}
      <main className="app-shell">
        <header className="app-header">
          <button className="sidebar-toggle" onClick={toggleSidebar} title="Toggle sidebar">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="3" y1="4" x2="15" y2="4" />
              <line x1="3" y1="9" x2="15" y2="9" />
              <line x1="3" y1="14" x2="15" y2="14" />
            </svg>
          </button>
          <div className="brand">ChatLLM Lab</div>
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

        <div className="warning-banner">Lembre-se, você precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

