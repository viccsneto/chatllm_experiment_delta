const API_BASE = window.location.origin;

/* ── Auth API ────────────────────────────────────────── */

function getToken() {
  return localStorage.getItem("chatllm_token");
}

function getEmail() {
  return localStorage.getItem("chatllm_email");
}

function saveAuth(token, email) {
  localStorage.setItem("chatllm_token", token);
  localStorage.setItem("chatllm_email", email);
}

function clearAuth() {
  localStorage.removeItem("chatllm_token");
  localStorage.removeItem("chatllm_email");
}

function authHeaders() {
  const token = getToken();
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function fetchMe() {
  const res = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { ...authHeaders() },
  });
  if (!res.ok) return null;
  return res.json();
}

async function apiLogout() {
  const res = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error("Falha ao fazer logout");
  clearAuth();
}

/* ── Session API ─────────────────────────────────────── */

async function fetchSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error("Falha ao carregar sessoes");
  const data = await res.json();
  return data.sessions;
}

async function createSession() {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error("Falha ao criar sessao");
  return res.json();
}

async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Falha ao excluir sessao");
}

async function fetchSessionHistory(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/history`);
  if (!res.ok) throw new Error("Falha ao carregar historico");
  return res.json();
}

async function suggestTitle(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/suggest-title`, {
    method: "POST",
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.title;
}

/* ── Chat API ────────────────────────────────────────── */

async function sendMessageStream({ message, sessionId, history, onDelta, onSessionId, signal }) {
  const body = { message, history };
  if (sessionId != null) body.session_id = sessionId;

  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const bodyText = await response.json().catch(() => ({}));
    const detail = bodyText?.detail || "Erro ao enviar mensagem para o servidor.";
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error("Streaming nao suportado no ambiente atual.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

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

      if (payload.delta) {
        onDelta(payload.delta);
      }

      // Capture session_id from first response if not set
      if (payload.session_id && typeof onSessionId === "function") {
        onSessionId(payload.session_id);
      }
    }
  }
}
