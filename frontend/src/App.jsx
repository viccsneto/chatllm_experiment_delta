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
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const initializedRef = useRef(false);

  // Check auth on mount
  useEffect(() => {
    (async () => {
      const result = await authCheck();
      if (result) {
        setUser(result);
      }
      setAuthLoading(false);
    })();
  }, []);

  // Load sessions when user is authenticated
  useEffect(() => {
    if (!user || initializedRef.current) return;
    initializedRef.current = true;
    (async () => {
      try {
        let list = await fetchSessions();
        if (list.length === 0) {
          const newSession = await createSession(null);
          list = [newSession];
        }
        setSessions(list);
        setActiveSessionId(list[0].id);
      } catch (err) {
        console.error("Falha ao carregar sessoes:", err);
        setError("Falha ao carregar sessoes. Recarregue a pagina.");
      }
    })();
  }, [user]);

  useEffect(() => {
    if (!activeSessionId) return;
    (async () => {
      try {
        const msgs = await fetchSessionMessages(activeSessionId);
        setMessages(
          msgs.length === 0
            ? [WELCOME_MESSAGE]
            : msgs.map((m) => ({
                id: `${m.id}-${Date.now()}`,
                role: m.role,
                content: m.content,
              }))
        );
      } catch {
        setMessages([WELCOME_MESSAGE]);
      }
    })();
  }, [activeSessionId]);

  const chatHistory = useMemo(
    () =>
      messages
        .filter((msg) => msg.id !== WELCOME_MESSAGE.id && (msg.role === "user" || msg.role === "assistant"))
        .map((msg) => ({ role: msg.role, content: msg.content })),
    [messages]
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

  const refreshSessions = useCallback(async () => {
    try {
      const list = await fetchSessions();
      setSessions(list);
    } catch {
      /* */
    }
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
      const result = await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId: activeSessionId,
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

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );

      if (result.sessionId && result.sessionId !== activeSessionId) {
        setActiveSessionId(result.sessionId);
      }
      await refreshSessions();
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

  const handleNewSession = async () => {
    try {
      const newSession = await createSession(null);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([WELCOME_MESSAGE]);
    } catch (err) {
      setError("Erro ao criar nova sessao.");
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      if (remaining.length === 0) {
        const newSession = await createSession(null);
        setSessions([newSession]);
        setActiveSessionId(newSession.id);
        setMessages([WELCOME_MESSAGE]);
      } else {
        setSessions(remaining);
        if (activeSessionId === sessionId) {
          setActiveSessionId(remaining[0].id);
        }
      }
    } catch (err) {
      setError("Erro ao excluir sessao.");
    }
  };

  const handleRenameSession = async (sessionId, title) => {
    try {
      await renameSession(sessionId, title);
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title } : s))
      );
    } catch {
      setError("Erro ao renomear sessao.");
    }
  };

  const handleAuthSuccess = (result) => {
    setUser({ id: null, email: result.email });
  };

  const handleLogout = () => {
    authLogout();
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([WELCOME_MESSAGE]);
    initializedRef.current = false;
  };

  // Show auth page while loading or if not authenticated
  if (authLoading) {
    return React.createElement("div", { className: "auth-page" },
      React.createElement("div", { className: "auth-card" },
        React.createElement("div", { className: "auth-brand" }, "ChatLLM Lab"),
        React.createElement("p", { style: { textAlign: "center", color: "#888" } }, "Verificando autenticacao...")
      )
    );
  }

  if (!user) {
    return React.createElement(AuthPage, { onAuthSuccess: handleAuthSuccess });
  }

  return (
    <div className="app-layout">
      {sidebarOpen && (
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={setActiveSessionId}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
        onRename={handleRenameSession}
      />
      )}

      <main className="app-shell">
        <header className="app-header">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Alternar barra lateral"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
              <line x1="4" y1="5" x2="16" y2="5" />
              <line x1="4" y1="10" x2="16" y2="10" />
              <line x1="4" y1="15" x2="16" y2="15" />
            </svg>
          </button>
          <div className="brand">ChatLLM Lab</div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{user?.email}</span>
            <button
              onClick={handleLogout}
              style={{
                border: "1px solid var(--border)",
                background: "transparent",
                borderRadius: "6px",
                padding: "4px 10px",
                fontSize: "0.8rem",
                cursor: "pointer",
                color: "var(--muted)",
              }}
              title="Sair"
            >
              Sair
            </button>
          </div>
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

