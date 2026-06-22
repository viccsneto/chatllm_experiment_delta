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
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Carrega sessoes e cria uma nova ao montar
  useEffect(() => {
    async function init() {
      try {
        const existing = await listSessions();
        setSessions(existing);
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        setCurrentSessionId(session.id);
      } catch {
        // Continua sem sessoes
      } finally {
        setInitializing(false);
      }
    }
    init();
  }, []);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
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

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const loadSessionMessages = useCallback(async (sessionId) => {
    setCurrentSessionId(sessionId);
    setSidebarOpen(false);
    setMessages([WELCOME_MESSAGE]);
    setError("");
    try {
      const msgs = await getSessionMessages(sessionId);
      if (msgs && msgs.length > 0) {
        setMessages(
          msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
        );
      }
    } catch {
      setError("Erro ao carregar mensagens da sessao.");
    }
  }, []);

  const handleDeleteSession = useCallback(async (sessionId, event) => {
    event.stopPropagation();
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (sessionId === currentSessionId) {
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        setCurrentSessionId(session.id);
        setMessages([WELCOME_MESSAGE]);
      }
    } catch {
      setError("Erro ao deletar sessao.");
    }
  }, [currentSessionId]);

  const handleNewSession = useCallback(async () => {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      setMessages([WELCOME_MESSAGE]);
      setError("");
    } catch {
      setError("Erro ao criar nova sessao.");
    }
  }, []);

  const handleSessionTitleClick = useCallback(async (sessionId) => {
    await loadSessionMessages(sessionId);
  }, [loadSessionMessages]);

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy || initializing) return;

    const sessionId = currentSessionId;
    if (!sessionId) return;

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [...prev, userMessage, { id: assistantMessageId, role: "assistant", content: "" }]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: `${msg.content}${delta}` } : msg
            )
          );
        },
        onDone: async () => {
          const updated = await listSessions();
          setSessions(updated);
        },
      });

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

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="header-left">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen((prev) => !prev)} aria-label={sidebarOpen ? "Reduzir" : "Expandir"}>
            {sidebarOpen ? "Reduzir" : "Expandir"}
          </button>
        </div>
        <div className="brand">
          {sessions.find((s) => s.id === currentSessionId)?.title || "ChatLLM Lab"}
        </div>
        <div className="header-right" />
      </header>

      <div className="app-body">
        {sidebarOpen && (
          <aside className="sidebar">
            <div className="sidebar-header">
              <span className="sidebar-title">Sessoes</span>
              <button className="sidebar-new-btn" onClick={handleNewSession} aria-label="Nova sessao">+</button>
            </div>
            <div className="sidebar-list">
              {sessions.length === 0 && <div className="sidebar-empty">Nenhuma sessao</div>}
              {sessions.map((s) => (
                <div key={s.id} className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`} onClick={() => handleSessionTitleClick(s.id)}>
                  <span className="sidebar-item-title" title={s.title || "Sem titulo"}>{s.title || "Sem titulo"}</span>
                  <button className="sidebar-item-delete" onClick={(e) => handleDeleteSession(s.id, e)} aria-label="Deletar sessao" title="Deletar">&times;</button>
                </div>
              ))}
            </div>
          </aside>
        )}

        <div className="chat-area">
          <section className="messages" aria-live="polite" ref={messagesRef}>
            <div className="messages-inner">
              {messages.map((msg) => (
                <article key={msg.id} className={`bubble ${msg.role}`}>
                  <MessageContent content={msg.content} />
                </article>
              ))}
            </div>
          </section>

          <Composer text={text} busy={busy} error={error} onChangeText={setText} onSubmit={onSubmit} onStop={onStop} />
        </div>
      </div>

      <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

