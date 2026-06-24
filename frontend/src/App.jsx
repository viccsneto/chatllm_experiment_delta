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
  const [user, setUser] = useState(null); // { token, email } | null
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  /* ── Check existing auth on mount ───────────────── */
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setCheckingAuth(false);
      return;
    }
    fetchMe()
      .then((data) => {
        if (data) {
          setUser({ token, email: data.email });
        } else {
          clearAuth();
        }
      })
      .catch(() => clearAuth())
      .finally(() => setCheckingAuth(false));
  }, []);

  /* ── Load sessions when user is set ─────────────── */
  useEffect(() => {
    if (!user) return;
    fetchSessions()
      .then((sess) => {
        setSessions(sess);
        if (sess.length > 0) {
          loadSession(sess[0].id, false);
        }
      })
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  /* ── Login handler ──────────────────────────────── */
  const handleLogin = useCallback((token, email) => {
    saveAuth(token, email);
    setUser({ token, email });
  }, []);

  /* ── Logout handler ─────────────────────────────── */
  const handleLogout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {}
    clearAuth();
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([WELCOME_MESSAGE]);
  }, []);

  /* ── Load a session's history ───────────────────── */
  const loadSession = useCallback(async (sessionId, fetchHistory = true) => {
    setActiveSessionId(sessionId);
    if (fetchHistory) {
      try {
        const history = await fetchSessionHistory(sessionId);
        if (history.length === 0) {
          setMessages([WELCOME_MESSAGE]);
        } else {
          setMessages(
            history.map((m) => ({
              id: createMessageId(),
              role: m.role,
              content: m.content,
            }))
          );
        }
      } catch {
        setMessages([WELCOME_MESSAGE]);
      }
    }
  }, []);

  /* ── Reload session list ────────────────────────── */
  const refreshSessions = useCallback(async () => {
    try {
      const sess = await fetchSessions();
      setSessions(sess);
    } catch {}
  }, []);

  /* ── Create new session ─────────────────────────── */
  const handleCreateSession = useCallback(async () => {
    try {
      const sess = await createSession();
      setSessions((prev) => [sess, ...prev]);
      setMessages([WELCOME_MESSAGE]);
      setError("");
      setActiveSessionId(sess.id);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  /* ── Delete session ─────────────────────────────── */
  const handleDeleteSession = useCallback(
    async (sessionId) => {
      try {
        await deleteSession(sessionId);
        const updated = sessions.filter((s) => s.id !== sessionId);
        setSessions(updated);
        if (activeSessionId === sessionId) {
          if (updated.length > 0) {
            loadSession(updated[0].id, true);
          } else {
            setActiveSessionId(null);
            setMessages([WELCOME_MESSAGE]);
          }
        }
      } catch (err) {
        setError(err.message);
      }
    },
    [sessions, activeSessionId, loadSession]
  );

  /* ── Suggest title after first exchange ──────────── */
  const trySuggestTitle = useCallback(
    async (sessionId) => {
      if (!sessionId) return;
      const session = sessions.find((s) => s.id === sessionId);
      if (session && session.title) return;

      try {
        const title = await suggestTitle(sessionId);
        if (title) {
          setSessions((prev) =>
            prev.map((s) => (s.id === sessionId ? { ...s, title } : s))
          );
        }
      } catch {}
    },
    [sessions]
  );

  /* ── Stop streaming ─────────────────────────────── */
  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  /* ── Submit message ─────────────────────────────── */
  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      try {
        const sess = await createSession();
        setSessions((prev) => [sess, ...prev]);
        setActiveSessionId(sess.id);
        sessionId = sess.id;
      } catch (err) {
        setError(err.message);
        return;
      }
    }

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

    const isFirstUserMessage = chatHistory.filter((m) => m.role === "user").length === 0;

    try {
      await sendMessageStream({
        message: cleaned,
        sessionId,
        history: chatHistory,
        signal: abortController.signal,
        onSessionId: (sid) => {
          if (!activeSessionId) {
            setActiveSessionId(sid);
            sessionId = sid;
          }
        },
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

      if (isFirstUserMessage && sessionId) {
        trySuggestTitle(sessionId);
      }

      refreshSessions();
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

  /* ── Loading / Login / Chat UI ──────────────────── */
  if (checkingAuth) {
    return (
      <div className="login-container" style={{ alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--muted)" }}>Verificando autenticacao...</p>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={(id) => loadSession(id, true)}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
      />
      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
          <div className="header-right">
            <span className="header-email" title={user.email}>
              {user.email}
            </span>
            <button className="header-logout-btn" onClick={handleLogout} aria-label="Sair">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
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

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

