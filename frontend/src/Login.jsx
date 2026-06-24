const { useState } = React;

function Login({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const cleaned = email.trim().toLowerCase();
    if (!cleaned || !password) {
      setError("Preencha todos os campos.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/signup";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: cleaned, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Erro ao autenticar.");
        return;
      }

      onLogin(data.token, data.email);
    } catch (err) {
      setError(err.message || "Erro de conexao com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode((m) => (m === "login" ? "signup" : "login"));
    setError("");
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1 className="login-title">ChatLLM Lab</h1>
        <p className="login-subtitle">
          {mode === "login" ? "Entre com sua conta" : "Crie uma nova conta"}
        </p>

        {error && <div className="login-error">{error}</div>}

        <input
          className="login-input"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <input
          className="login-input"
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
        />

        <button className="login-btn" type="submit" disabled={loading}>
          {loading
            ? "Aguarde..."
            : mode === "login"
            ? "Entrar"
            : "Cadastrar"}
        </button>

        <p className="login-toggle" onClick={toggleMode}>
          {mode === "login"
            ? "Nao tem conta? Cadastre-se"
            : "Ja tem conta? Entre"}
        </p>
      </form>
    </div>
  );
}
