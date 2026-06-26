const { useState } = React;

function AuthPage({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const switchMode = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "login") {
        const result = await authLogin(email, password);
        onAuthSuccess(result);
      } else {
        await authSignup(email, password, passwordConfirm);
        // After signup, automatically log in
        const result = await authLogin(email, password);
        onAuthSuccess(result);
      }
    } catch (err) {
      setError(err.message || "Erro inesperado. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  var isLogin = mode === "login";

  return React.createElement("div", { className: "auth-page" },
    React.createElement("div", { className: "auth-card" },
      React.createElement("div", { className: "auth-brand" }, "ChatLLM Lab"),
      React.createElement("h2", { className: "auth-title" }, isLogin ? "Entrar" : "Cadastrar"),
      React.createElement("form", { onSubmit: handleSubmit },
        error && React.createElement("div", { className: "auth-error" }, error),

        React.createElement("div", { className: "auth-field" },
          React.createElement("label", { htmlFor: "auth-email" }, "Email"),
          React.createElement("input", {
            id: "auth-email",
            type: "text",
            inputMode: "email",
            placeholder: "seu@email.com",
            value: email,
            onChange: function (ev) { setEmail(ev.target.value); },
            required: true,
            autoFocus: true,
          })
        ),

        React.createElement("div", { className: "auth-field" },
          React.createElement("label", { htmlFor: "auth-password" }, "Senha"),
          React.createElement("input", {
            id: "auth-password",
            type: "password",
            placeholder: isLogin ? "Sua senha" : "Minimo 8 caracteres, 1 numero, 1 especial",
            value: password,
            onChange: function (ev) { setPassword(ev.target.value); },
            required: true,
          })
        ),

        !isLogin && React.createElement("div", { className: "auth-field" },
          React.createElement("label", { htmlFor: "auth-password-confirm" }, "Confirmar senha"),
          React.createElement("input", {
            id: "auth-password-confirm",
            type: "password",
            placeholder: "Repita a senha",
            value: passwordConfirm,
            onChange: function (ev) { setPasswordConfirm(ev.target.value); },
            required: true,
          })
        ),

        React.createElement("button", {
          type: "submit",
          className: "auth-submit",
          disabled: loading,
        }, loading ? "Aguarde..." : (isLogin ? "Entrar" : "Cadastrar"))
      ),

      React.createElement("p", { className: "auth-switch" },
        isLogin ? "Nao tem conta? " : "Ja tem conta? ",
        React.createElement("a", { href: "#", onClick: function (ev) { ev.preventDefault(); switchMode(); } },
          isLogin ? "Cadastre-se" : "Fazer login")
      )
    )
  );
}