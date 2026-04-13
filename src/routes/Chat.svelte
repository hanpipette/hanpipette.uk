<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { link } from 'svelte-spa-router';
  import {
    login,
    me,
    fetchMessages,
    openChatSocket,
    updateNickname,
    getToken,
    setToken,
    clearToken,
    type Message,
    type User,
  } from '../lib/api';

  let user: User | null = $state(null);
  let messages: Message[] = $state([]);
  let username = $state('');
  let password = $state('');
  let draft = $state('');
  let nicknameDraft = $state('');
  let editingNick = $state(false);
  let loginError = $state('');
  let nickError = $state('');
  let connecting = $state(false);
  let connected = $state(false);
  let booting = $state(true);

  let socket: WebSocket | null = null;
  let scrollEl: HTMLDivElement | null = $state(null);

  async function scrollBottom() {
    await tick();
    if (scrollEl) scrollEl.scrollTop = scrollEl.scrollHeight;
  }

  async function bootstrap() {
    const token = getToken();
    if (!token) {
      booting = false;
      return;
    }
    try {
      user = await me();
      await loadHistoryAndConnect(token);
    } catch {
      clearToken();
      user = null;
    } finally {
      booting = false;
    }
  }

  async function loadHistoryAndConnect(token: string) {
    try {
      messages = await fetchMessages();
      await scrollBottom();
    } catch {
      messages = [];
    }
    connect(token);
  }

  function connect(token: string) {
    if (socket) {
      socket.close();
      socket = null;
    }
    connecting = true;
    const ws = openChatSocket(token);
    socket = ws;
    ws.onopen = () => {
      connecting = false;
      connected = true;
    };
    ws.onclose = () => {
      connecting = false;
      connected = false;
    };
    ws.onerror = () => {
      connecting = false;
      connected = false;
    };
    ws.onmessage = async (ev) => {
      try {
        const msg = JSON.parse(ev.data) as Message;
        messages = [...messages, msg];
        await scrollBottom();
      } catch {}
    };
  }

  async function onLogin(e: Event) {
    e.preventDefault();
    loginError = '';
    try {
      const res = await login(username.trim(), password);
      setToken(res.token);
      user = res.user;
      password = '';
      await loadHistoryAndConnect(res.token);
    } catch (err: any) {
      loginError = err?.message || 'ログイン失敗';
    }
  }

  function onLogout() {
    if (socket) socket.close();
    socket = null;
    clearToken();
    user = null;
    messages = [];
    connected = false;
  }

  function sendDraft() {
    const content = draft.trim();
    if (!content || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ content }));
    draft = '';
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendDraft();
    }
  }

  function startEditNick() {
    if (!user) return;
    nicknameDraft = user.nickname;
    editingNick = true;
    nickError = '';
  }

  async function saveNick() {
    const next = nicknameDraft.trim();
    if (!next || !user) {
      editingNick = false;
      return;
    }
    if (next === user.nickname) {
      editingNick = false;
      return;
    }
    try {
      user = await updateNickname(next);
      editingNick = false;
    } catch (err: any) {
      nickError = err?.message || '変更失敗';
    }
  }

  function formatTime(iso: string): string {
    const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'));
    return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  }

  onMount(() => {
    bootstrap();
  });

  onDestroy(() => {
    if (socket) socket.close();
  });
</script>

<svelte:head>
  <title>/chat — 秘密の部屋</title>
</svelte:head>

<main class="chat-page">
  <div class="scanlines" aria-hidden="true"></div>
  <div class="noise" aria-hidden="true"></div>
  <div class="vignette" aria-hidden="true"></div>

  <header class="chat-header">
    <a class="back-link" href="/" use:link>← home</a>
    <span class="chat-title">/chat — 地下室</span>
    {#if user}
      <button class="logout" onclick={onLogout}>logout</button>
    {:else}
      <span class="logout ghost">—</span>
    {/if}
  </header>

  {#if booting}
    <div class="panel center">
      <p class="loading">loading...</p>
    </div>
  {:else if !user}
    <form class="panel login" onsubmit={onLogin}>
      <h2>&gt; 認証が必要</h2>
      <p class="hint">あなたのユーザー名とパスワードを入力してください</p>
      <label>
        <span>username</span>
        <input
          type="text"
          bind:value={username}
          autocomplete="username"
          required
        />
      </label>
      <label>
        <span>password</span>
        <input
          type="password"
          bind:value={password}
          autocomplete="current-password"
          required
        />
      </label>
      {#if loginError}
        <p class="err">× {loginError}</p>
      {/if}
      <button type="submit" class="primary">enter</button>
      <p class="small">アカウントは管理者に依頼してください</p>
    </form>
  {:else}
    <section class="panel chat">
      <div class="chat-meta">
        <div class="who">
          {#if editingNick}
            <!-- svelte-ignore a11y_autofocus -->
            <input
              class="nick-input"
              bind:value={nicknameDraft}
              maxlength="32"
              autofocus
              onblur={saveNick}
              onkeydown={(e) => e.key === 'Enter' && saveNick()}
            />
          {:else}
            <button class="nick-btn" onclick={startEditNick} title="click to edit">
              {user.nickname}
            </button>
          {/if}
          <span class="handle">@{user.username}</span>
        </div>
        <div class="status">
          <span class="dot" class:on={connected} class:pending={connecting}></span>
          {connected ? 'online' : connecting ? 'connecting' : 'offline'}
        </div>
      </div>
      {#if nickError}
        <p class="err small">× {nickError}</p>
      {/if}

      <div class="messages" bind:this={scrollEl}>
        {#if messages.length === 0}
          <p class="empty">まだ何もない... 最初の声になって</p>
        {/if}
        {#each messages as msg (msg.id)}
          <article class="msg" class:mine={user && msg.user_id === user.id}>
            <header>
              <span class="nick">{msg.nickname}</span>
              <time>{formatTime(msg.created_at)}</time>
            </header>
            <p>{msg.content}</p>
          </article>
        {/each}
      </div>

      <div class="composer">
        <textarea
          placeholder="type something..."
          bind:value={draft}
          onkeydown={onKey}
          rows="2"
          disabled={!connected}
        ></textarea>
        <button
          class="primary"
          onclick={sendDraft}
          disabled={!connected || !draft.trim()}
        >
          送信
        </button>
      </div>
    </section>
  {/if}
</main>

<style>
  .chat-page {
    min-height: 100vh;
    background: radial-gradient(1200px 800px at 50% 0%, #1a0e25 0%, #0a0610 70%);
    color: var(--text);
    font-family: var(--sans);
    padding: 24px 16px 48px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    position: relative;
  }
  .chat-header {
    width: min(760px, 100%);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-family: var(--dot);
    font-size: 13px;
    color: var(--muted);
  }
  .chat-title {
    color: var(--pink);
    letter-spacing: 0.08em;
  }
  .back-link,
  .logout {
    color: var(--muted);
    text-decoration: none;
    background: none;
    border: 1px solid var(--line);
    padding: 6px 10px;
    font-family: var(--dot);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .back-link:hover,
  .logout:hover {
    color: var(--pink);
    border-color: var(--pink);
  }
  .logout.ghost {
    visibility: hidden;
  }
  .panel {
    width: min(760px, 100%);
    background: var(--win-bg);
    border: 1px solid var(--win-border);
    box-shadow: 0 0 40px rgba(255, 46, 139, 0.08),
      inset 0 0 30px rgba(255, 118, 189, 0.04);
    backdrop-filter: blur(4px);
    padding: 28px;
  }
  .panel.center {
    text-align: center;
  }
  .loading {
    font-family: var(--dot);
    color: var(--muted);
    animation: blink 1s infinite;
  }
  @keyframes blink {
    50% { opacity: 0.3; }
  }
  .login {
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-width: 420px;
  }
  .login h2 {
    font-family: var(--dot);
    color: var(--pink);
    font-size: 18px;
    margin: 0;
    letter-spacing: 0.04em;
  }
  .hint {
    color: var(--muted);
    font-size: 13px;
    margin: -4px 0 4px;
  }
  .login label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-family: var(--dot);
    font-size: 12px;
    color: var(--muted);
  }
  input,
  textarea {
    background: #0a0610;
    border: 1px solid var(--line);
    color: var(--text);
    padding: 10px 12px;
    font-family: var(--sans);
    font-size: 14px;
    outline: none;
    transition: border-color 0.15s;
  }
  input:focus,
  textarea:focus {
    border-color: var(--pink);
  }
  .primary {
    background: linear-gradient(135deg, var(--hot-pink), var(--pink));
    color: #0a0610;
    border: none;
    padding: 10px 14px;
    font-family: var(--dot);
    font-size: 13px;
    letter-spacing: 0.06em;
    cursor: pointer;
    transition: filter 0.15s;
  }
  .primary:hover {
    filter: brightness(1.15);
  }
  .primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .err {
    color: var(--red);
    font-size: 13px;
    margin: 0;
  }
  .small {
    font-size: 11px;
    color: var(--muted);
  }
  .chat {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 560px;
  }
  .chat-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 1px dashed var(--line);
  }
  .who {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }
  .nick-btn {
    background: none;
    border: 1px dashed transparent;
    color: var(--pink);
    font-family: var(--sans);
    font-size: 16px;
    font-weight: 600;
    padding: 2px 6px;
    cursor: pointer;
  }
  .nick-btn:hover {
    border-color: var(--pink);
  }
  .nick-input {
    font-size: 16px;
    padding: 2px 6px;
    width: 160px;
  }
  .handle {
    color: var(--muted);
    font-size: 12px;
    font-family: var(--dot);
  }
  .status {
    font-family: var(--dot);
    font-size: 12px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--red);
    box-shadow: 0 0 6px currentColor;
  }
  .dot.pending {
    background: var(--warn);
  }
  .dot.on {
    background: #66ff99;
  }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 8px 4px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 360px;
    max-height: 540px;
  }
  .messages::-webkit-scrollbar {
    width: 6px;
  }
  .messages::-webkit-scrollbar-thumb {
    background: var(--win-border);
  }
  .empty {
    color: var(--muted);
    text-align: center;
    margin: auto;
    font-family: var(--dot);
    font-size: 13px;
  }
  .msg {
    background: rgba(255, 118, 189, 0.05);
    border-left: 2px solid var(--win-border);
    padding: 8px 12px;
    max-width: 80%;
  }
  .msg.mine {
    align-self: flex-end;
    border-left: none;
    border-right: 2px solid var(--pink);
    background: rgba(255, 46, 139, 0.1);
  }
  .msg header {
    display: flex;
    gap: 8px;
    align-items: baseline;
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 2px;
  }
  .msg .nick {
    color: var(--pink);
    font-weight: 600;
  }
  .msg p {
    margin: 0;
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .composer {
    display: flex;
    gap: 8px;
    align-items: stretch;
  }
  .composer textarea {
    flex: 1;
    resize: none;
    font-family: var(--sans);
  }
  .composer .primary {
    padding: 0 18px;
  }
</style>
