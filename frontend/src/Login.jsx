const { useState } = React;

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const cleanedEmail = email.trim();
    const cleanedPassword = password.trim();
    if (!cleanedEmail || !cleanedPassword) {
      setError("Preencha email e senha.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === "login" ? "login" : "signup";
      const response = await fetch(`${window.location.origin}/api/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: cleanedEmail, password: cleanedPassword }),
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || "Erro na autenticacao.");
        return;
      }

      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("auth_email", data.email);
      onLogin(data.token, data.email);
    } catch (err) {
      setError("Erro de conexao com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError("");
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">ChatLLM Lab</div>
        <h2 className="login-title">{mode === "login" ? "Entrar" : "Criar conta"}</h2>

        <form onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              disabled={loading}
              autoFocus
            />
          </div>
          <div className="login-field">
            <label htmlFor="login-password">Senha</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Sua senha"
              disabled={loading}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}
          </button>
        </form>

        <div className="login-switch">
          {mode === "login" ? (
            <span>
              Nao tem conta?{" "}
              <button className="link-btn" onClick={switchMode} disabled={loading}>
                Cadastre-se
              </button>
            </span>
          ) : (
            <span>
              Ja tem conta?{" "}
              <button className="link-btn" onClick={switchMode} disabled={loading}>
                Fazer login
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}