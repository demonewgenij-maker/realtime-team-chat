"use strict";

// --- Tiny state -----------------------------------------------------------
const state = {
  token: localStorage.getItem("token") || null,
  username: localStorage.getItem("username") || null,
  userId: Number(localStorage.getItem("userId")) || null,
  channelId: null,
  ws: null,
};

// --- DOM helpers ----------------------------------------------------------
const $ = (id) => document.getElementById(id);

/** Build an element with text set via textContent (no raw HTML injection). */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text; // XSS-safe: textContent only
  return node;
}

// --- API ------------------------------------------------------------------
async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `HTTP ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

// --- Auth -----------------------------------------------------------------
function saveSession(data) {
  state.token = data.access_token;
  state.username = data.username;
  state.userId = data.user_id;
  localStorage.setItem("token", state.token);
  localStorage.setItem("username", state.username);
  localStorage.setItem("userId", String(state.userId));
}

function clearSession() {
  state.token = state.username = state.userId = state.channelId = null;
  localStorage.clear();
  if (state.ws) state.ws.close();
  state.ws = null;
}

async function doAuth(path) {
  const username = $("auth-username").value.trim().toLowerCase();
  const password = $("auth-password").value;
  const err = $("auth-error");
  err.hidden = true;
  try {
    const data = await api(path, { method: "POST", body: { username, password }, auth: false });
    saveSession(data);
    enterChat();
  } catch (e) {
    err.textContent = e.message;
    err.hidden = false;
  }
}

// --- Channels & messages --------------------------------------------------
async function loadChannels() {
  const channels = await api("/api/channels");
  const list = $("channel-list");
  list.replaceChildren();
  for (const ch of channels) {
    const li = el("li", "channel", `# ${ch.name}`);
    li.dataset.id = ch.id;
    li.addEventListener("click", () => selectChannel(ch.id, ch.name));
    list.appendChild(li);
  }
  if (!state.channelId && channels.length) {
    selectChannel(channels[0].id, channels[0].name);
  }
}

async function selectChannel(id, name) {
  state.channelId = id;
  $("channel-header").textContent = `# ${name}`;
  for (const li of document.querySelectorAll(".channel")) {
    li.classList.toggle("active", Number(li.dataset.id) === id);
  }
  const messages = await api(`/api/channels/${id}/messages?limit=50`);
  const ul = $("messages");
  ul.replaceChildren();
  messages.forEach(renderMessage);
  ul.scrollTop = ul.scrollHeight;
  subscribe(id);
}

function renderMessage(m) {
  const li = el("li", "message");
  li.appendChild(el("span", "author", m.username));
  li.appendChild(el("span", "content", m.content)); // textContent -> safe
  const ul = $("messages");
  const atBottom = ul.scrollHeight - ul.scrollTop - ul.clientHeight < 40;
  ul.appendChild(li);
  if (atBottom) ul.scrollTop = ul.scrollHeight;
}

async function sendMessage(e) {
  e.preventDefault();
  const input = $("message-input");
  const content = input.value.trim();
  if (!content || !state.channelId) return;
  input.value = "";
  try {
    await api(`/api/channels/${state.channelId}/messages`, {
      method: "POST",
      body: { content },
    });
    // The message arrives back via WebSocket broadcast; no optimistic render.
  } catch (err) {
    input.value = content;
  }
}

// --- WebSocket ------------------------------------------------------------
function connectWs() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws?token=${encodeURIComponent(state.token)}`);
  ws.addEventListener("message", (ev) => {
    const data = JSON.parse(ev.data);
    if (data.type === "message" && data.channel_id === state.channelId) {
      renderMessage(data.message);
    }
  });
  ws.addEventListener("close", () => {
    // Reconnect with backoff while still logged in.
    if (state.token) setTimeout(connectWs, 1500);
  });
  ws.addEventListener("open", () => {
    if (state.channelId) subscribe(state.channelId);
  });
  state.ws = ws;
}

function subscribe(channelId) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ action: "subscribe", channel_id: channelId }));
  }
}

// --- Screens --------------------------------------------------------------
function enterChat() {
  $("auth-screen").hidden = true;
  $("chat-screen").hidden = false;
  $("who").textContent = state.username;
  connectWs();
  loadChannels();
}

function enterAuth() {
  $("chat-screen").hidden = true;
  $("auth-screen").hidden = false;
}

// --- Wiring ---------------------------------------------------------------
$("btn-login").addEventListener("click", () => doAuth("/api/auth/login"));
$("btn-register").addEventListener("click", () => doAuth("/api/auth/register"));
$("btn-logout").addEventListener("click", () => {
  clearSession();
  enterAuth();
});
$("message-form").addEventListener("submit", sendMessage);
$("new-channel-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("new-channel-name").value.trim();
  if (!name) return;
  try {
    await api("/api/channels", { method: "POST", body: { name } });
    $("new-channel-name").value = "";
    await loadChannels();
  } catch (_) {}
});

if (state.token) enterChat();
else enterAuth();

// Register the service worker (PWA offline shell).
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
