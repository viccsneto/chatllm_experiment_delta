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

  // Auth state
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isSignup, setIsSignup] = useState(false);
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Check auth on mount + load sessions
  useEffect(() => {
    async function init() {
      try {
        const userData = await checkAuth();
        if (userData) {
          setUser(userData);
          localStorage.setItem("auth_token", userData.token || localStorage.getItem("auth_token"));
        }
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

  const resetToNewSession = useCallback(async () => {
    try {
      const session = await createSession();
      setSessions([session]);
      setCurrentSessionId(session.id);
      setMessages([WELCOME_MESSAGE]);
    } catch {
      setError("Erro ao criar sessao.");
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

  // ── Auth handlers ──────────────────────────────────────────────────────

  const handleOpenLogin = () => {
    setIsSignup(false);
    setAuthEmail("");
    setAuthPassword("");
    setAuthError("");
    setShowAuthModal(true);
  };

  const handleOpenSignup = () => {
    setIsSignup(true);
    setAuthEmail("");
    setAuthPassword("");
    setAuthError("");
    setShowAuthModal(true);
  };

  const handleCloseAuth = () => {
    setShowAuthModal(false);
    setAuthError("");
  };

  const switchToSignup = () => {
    setIsSignup(true);
    setAuthError("");
  };

  const switchToLogin = () => {
    setIsSignup(false);
    setAuthError("");
  };

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    const email = authEmail.trim();
    const password = authPassword.trim();
    if (!email || !password) return;

    setAuthBusy(true);
    setAuthError("");

    try {
      let result;
      if (isSignup) {
        result = await signup(email, password);
      } else {
        result = await login(email, password);
      }

      // Salva token
      localStorage.setItem("auth_token", result.token);
      setUser({ user_id: result.user_id, email: result.email });
      setShowAuthModal(false);

      // 1. Remove sessoes nao proprietarias do banco
      try { await deleteUnownedSessions(); } catch {}

      // 2. Carrega sessoes do usuario
      const userSessions = await listSessions();
      if (userSessions.length > 0) {
        setSessions(userSessions);
        setCurrentSessionId(userSessions[0].id);
        await loadSessionMessages(userSessions[0].id);
      } else {
        await resetToNewSession();
      }
    } catch (err) {
      setAuthError(err.message || "Erro na autenticacao");
    } finally {
      setAuthBusy(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {}
    localStorage.removeItem("auth_token");
    setUser(null);
    await resetToNewSession();
  };

  // ── Submit ──────────────────────────────────────────────────────────────

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
        <div className="header-right">
          {user ? (
            <div className="header-user-area">
              <span className="header-user-email" title={user.email}>{user.email.split("@")[0]}</span>
              <button className="auth-btn logout-btn" onClick={handleLogout}>Logout</button>
            </div>
          ) : (
            <button className="auth-btn login-btn" onClick={handleOpenLogin}>Login</button>
          )}
        </div>
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

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="auth-overlay" onClick={handleCloseAuth}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="auth-title">{isSignup ? "Cadastro" : "Login"}</h2>
            <form onSubmit={handleAuthSubmit}>
              <input
                className="auth-input"
                type="email"
                placeholder="Email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                disabled={authBusy}
                autoFocus
                required
              />
              <input
                className="auth-input"
                type="password"
                placeholder="Senha"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                disabled={authBusy}
                minLength={6}
                required
              />
              {authError && <div className="auth-error">{authError}</div>}
              <button className="auth-submit" type="submit" disabled={authBusy}>
                {authBusy ? "Aguarde..." : isSignup ? "Cadastrar" : "Entrar"}
              </button>
            </form>
            <div className="auth-switch">
              {isSignup ? (
                <span>Ja tem conta? <button className="auth-link" onClick={switchToLogin}>Entre</button></span>
              ) : (
                <span>Nao tem conta? <button className="auth-link" onClick={switchToSignup}>Cadastre-se</button></span>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

