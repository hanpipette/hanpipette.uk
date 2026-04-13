<script lang="ts">
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import {
    login,
    me,
    listUsers,
    createUser,
    deleteUser,
    getToken,
    setToken,
    clearToken,
    type User,
  } from '../lib/api';

  let currentUser: User | null = $state(null);
  let users: User[] = $state([]);
  let booting = $state(true);

  let loginUsername = $state('');
  let loginPassword = $state('');
  let loginError = $state('');

  let newUsername = $state('');
  let newPassword = $state('');
  let newNickname = $state('');
  let newIsAdmin = $state(false);
  let createError = $state('');
  let busy = $state(false);

  async function bootstrap() {
    const token = getToken();
    if (!token) {
      booting = false;
      return;
    }
    try {
      const u = await me();
      if (!u.is_admin) {
        booting = false;
        return;
      }
      currentUser = u;
      await refresh();
    } catch {
      clearToken();
    } finally {
      booting = false;
    }
  }

  async function refresh() {
    try {
      users = await listUsers();
    } catch (err: any) {
      createError = err?.message || 'failed to load users';
    }
  }

  async function onLogin(e: Event) {
    e.preventDefault();
    loginError = '';
    try {
      const res = await login(loginUsername.trim(), loginPassword);
      if (!res.user.is_admin) {
        loginError = 'Admin 권한이 없습니다';
        return;
      }
      setToken(res.token);
      currentUser = res.user;
      loginPassword = '';
      await refresh();
    } catch (err: any) {
      loginError = err?.message || 'login failed';
    }
  }

  function logout() {
    clearToken();
    currentUser = null;
    users = [];
  }

  async function onCreate(e: Event) {
    e.preventDefault();
    createError = '';
    busy = true;
    try {
      await createUser({
        username: newUsername.trim(),
        password: newPassword,
        nickname: newNickname.trim() || undefined,
        is_admin: newIsAdmin,
      });
      newUsername = '';
      newPassword = '';
      newNickname = '';
      newIsAdmin = false;
      await refresh();
    } catch (err: any) {
      createError = err?.message || 'create failed';
    } finally {
      busy = false;
    }
  }

  async function onDelete(id: number, username: string) {
    if (!confirm(`${username} 계정을 삭제할까요?`)) return;
    try {
      await deleteUser(id);
      await refresh();
    } catch (err: any) {
      createError = err?.message || 'delete failed';
    }
  }

  onMount(bootstrap);
</script>

<svelte:head>
  <title>/admin — 管理</title>
</svelte:head>

<main class="admin-page">
  <div class="scanlines" aria-hidden="true"></div>
  <div class="noise" aria-hidden="true"></div>
  <div class="vignette" aria-hidden="true"></div>

  <header class="admin-header">
    <a class="back-link" href="/" use:link>← home</a>
    <span class="title">/admin — 管理者</span>
    {#if currentUser}
      <button class="logout" onclick={logout}>logout</button>
    {:else}
      <span class="logout ghost">—</span>
    {/if}
  </header>

  {#if booting}
    <div class="panel center">
      <p class="loading">loading...</p>
    </div>
  {:else if !currentUser}
    <form class="panel login" onsubmit={onLogin}>
      <h2>&gt; 管理者認証</h2>
      <label>
        <span>admin username</span>
        <input
          type="text"
          bind:value={loginUsername}
          autocomplete="username"
          required
        />
      </label>
      <label>
        <span>password</span>
        <input
          type="password"
          bind:value={loginPassword}
          autocomplete="current-password"
          required
        />
      </label>
      {#if loginError}
        <p class="err">× {loginError}</p>
      {/if}
      <button type="submit" class="primary">sign in</button>
    </form>
  {:else}
    <section class="panel">
      <h2>&gt; 새 유저 만들기</h2>
      <form class="create" onsubmit={onCreate}>
        <label>
          <span>username</span>
          <input type="text" bind:value={newUsername} required />
        </label>
        <label>
          <span>password</span>
          <input type="password" bind:value={newPassword} required minlength="4" />
        </label>
        <label>
          <span>nickname (optional)</span>
          <input type="text" bind:value={newNickname} />
        </label>
        <label class="check">
          <input type="checkbox" bind:checked={newIsAdmin} />
          <span>관리자 권한 부여</span>
        </label>
        {#if createError}
          <p class="err">× {createError}</p>
        {/if}
        <button type="submit" class="primary" disabled={busy}>
          {busy ? '...' : 'create'}
        </button>
      </form>
    </section>

    <section class="panel">
      <h2>&gt; 유저 목록 ({users.length})</h2>
      <div class="user-list">
        {#each users as u (u.id)}
          <div class="user-row">
            <div class="info">
              <span class="u-nick">{u.nickname}</span>
              <span class="u-name">@{u.username}</span>
              {#if u.is_admin}
                <span class="u-badge">ADMIN</span>
              {/if}
            </div>
            {#if currentUser && u.id !== currentUser.id}
              <button class="danger" onclick={() => onDelete(u.id, u.username)}>
                delete
              </button>
            {:else}
              <span class="self">you</span>
            {/if}
          </div>
        {/each}
      </div>
    </section>
  {/if}
</main>

<style>
  .admin-page {
    min-height: 100vh;
    background: radial-gradient(1200px 800px at 50% 0%, #1a0e25 0%, #0a0610 70%);
    color: var(--text);
    font-family: var(--sans);
    padding: 24px 16px 48px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }
  .admin-header {
    width: min(760px, 100%);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--dot);
    font-size: 13px;
    color: var(--muted);
  }
  .title {
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
    box-shadow: 0 0 40px rgba(255, 46, 139, 0.08);
    backdrop-filter: blur(4px);
    padding: 24px 28px;
  }
  .panel.center {
    text-align: center;
  }
  .panel h2 {
    font-family: var(--dot);
    color: var(--pink);
    font-size: 16px;
    margin: 0 0 16px;
    letter-spacing: 0.04em;
  }
  .loading {
    font-family: var(--dot);
    color: var(--muted);
  }
  .login {
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-width: 420px;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-family: var(--dot);
    font-size: 12px;
    color: var(--muted);
  }
  label.check {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }
  input[type='text'],
  input[type='password'] {
    background: #0a0610;
    border: 1px solid var(--line);
    color: var(--text);
    padding: 10px 12px;
    font-family: var(--sans);
    font-size: 14px;
    outline: none;
  }
  input[type='text']:focus,
  input[type='password']:focus {
    border-color: var(--pink);
  }
  .create {
    display: flex;
    flex-direction: column;
    gap: 12px;
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
    align-self: flex-start;
  }
  .primary:hover {
    filter: brightness(1.15);
  }
  .primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .danger {
    background: transparent;
    color: var(--red);
    border: 1px solid var(--red);
    padding: 6px 10px;
    font-family: var(--dot);
    font-size: 11px;
    cursor: pointer;
  }
  .danger:hover {
    background: var(--red);
    color: #0a0610;
  }
  .self {
    font-family: var(--dot);
    font-size: 11px;
    color: var(--muted);
  }
  .err {
    color: var(--red);
    font-size: 13px;
    margin: 0;
  }
  .user-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .user-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border: 1px dashed var(--line);
    background: rgba(255, 118, 189, 0.03);
  }
  .info {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }
  .u-nick {
    color: var(--text);
    font-weight: 600;
  }
  .u-name {
    color: var(--muted);
    font-family: var(--dot);
    font-size: 12px;
  }
  .u-badge {
    background: var(--pink);
    color: #0a0610;
    font-family: var(--dot);
    font-size: 10px;
    padding: 2px 6px;
    letter-spacing: 0.08em;
  }
</style>
