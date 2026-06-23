const { useState } = React;

function Login({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result;
      if (mode === "login") {
        result = await loginUser(email, password);
      } else {
        result = await registerUser(email, password);
      }
      localStorage.setItem("auth_token", result.token);
      localStorage.setItem("auth_email", result.email);
      localStorage.setItem("auth_user_id", result.user_id);
      onAuthSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode((prev) => (prev === "login" ? "register" : "login"));
    setError("");
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">ChatLLM Lab</h1>
        <h2 className="login-subtitle">
          {mode === "login" ? "Entrar" : "Criar conta"}
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              autoFocus
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimo 6 caracteres"
              required
              minLength={6}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading
              ? "Aguarde..."
              : mode === "login"
              ? "Entrar"
              : "Cadastrar"}
          </button>
        </form>

        <p className="login-switch">
          {mode === "login" ? (
            <>
              Nao tem conta?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); switchMode(); }}>
                Cadastre-se
              </a>
            </>
          ) : (
            <>
              Ja tem conta?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); switchMode(); }}>
                Fazer login
              </a>
            </>
          )}
        </p>
      </div>
    </div>
  );
}