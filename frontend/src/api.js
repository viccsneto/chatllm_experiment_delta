const API_BASE = window.location.origin;

// --- Auth helpers ---

function getToken() {
  return localStorage.getItem("chatllm_token");
}

function setToken(token) {
  if (token) {
    localStorage.setItem("chatllm_token", token);
  } else {
    localStorage.removeItem("chatllm_token");
  }
}

function getAuthHeaders() {
  const token = getToken();
  return token ? { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

async function sendMessageStream({ message, history, sessionId, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ message, history, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail || "Erro ao enviar mensagem para o servidor.";
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error("Streaming nao suportado no ambiente atual.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let sessionIdResolved = sessionId;
  let titleResolved = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      const line = rawEvent
        .split("\n")
        .find((part) => part.startsWith("data:"));
      if (!line) continue;

      const payloadText = line.slice(5).trim();
      if (!payloadText) continue;

      let payload;
      try {
        payload = JSON.parse(payloadText);
      } catch {
        continue;
      }

      if (payload.error) {
        throw new Error(payload.error);
      }

      if (payload.done) {
        sessionIdResolved = payload.session_id || sessionIdResolved;
        titleResolved = payload.title || null;
        break;
      }

      if (payload.delta) {
        onDelta(payload.delta);
      }
    }
  }

  return { sessionId: sessionIdResolved, title: titleResolved };
}

async function authSignup(email, password, passwordConfirm) {
  const res = await fetch(`${API_BASE}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, password_confirm: passwordConfirm }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(extractDetail(data));
  return data;
}

async function authLogin(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(extractDetail(data));
  setToken(data.access_token);
  return data;
}

async function authCheck() {
  const token = getToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE}/api/auth/check`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!res.ok) {
    setToken(null);
    return null;
  }
  return res.json();
}

function authLogout() {
  setToken(null);
}


async function fetchSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Erro ao listar sessoes");
  return res.json();
}

async function createSession(title) {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ title: title || null }),
  });
  if (!res.ok) throw new Error("Erro ao criar sessao");
  return res.json();
}

async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok && res.status !== 204) throw new Error("Erro ao excluir sessao");
}

async function renameSession(sessionId, title) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Erro ao renomear sessao");
  return res.json();
}

async function fetchSessionMessages(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Erro ao carregar mensagens");
  return res.json();
}

function extractDetail(data) {
  if (!data) return "Erro desconhecido";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    var msgs = [];
    for (var i = 0; i < data.detail.length; i++) {
      if (data.detail[i].msg) {
        var msg = data.detail[i].msg;
        if (msg.indexOf(", ") !== -1) msg = msg.split(", ").slice(1).join(", ");
        msgs.push(msg);
      }
    }
    return msgs.length > 0 ? msgs[0] : "Erro de validacao";
  }
  return "Erro desconhecido";
}
