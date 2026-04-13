export type User = {
  id: number;
  username: string;
  nickname: string;
  is_admin: boolean;
};

export type Message = {
  id: number;
  user_id: number;
  nickname: string;
  content: string;
  created_at: string;
};

const TOKEN_KEY = 'hanpipette.chat.token';
const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '');

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }
  if (auth) {
    const token = getToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function login(
  username: string,
  password: string,
): Promise<{ token: string; user: User }> {
  return request(
    '/api/auth/login',
    { method: 'POST', body: JSON.stringify({ username, password }) },
    false,
  );
}

export async function me(): Promise<User> {
  return request('/api/auth/me');
}

export async function updateNickname(nickname: string): Promise<User> {
  return request('/api/auth/nickname', {
    method: 'PATCH',
    body: JSON.stringify({ nickname }),
  });
}

export async function fetchMessages(beforeId?: number): Promise<Message[]> {
  const qs = beforeId ? `?before_id=${beforeId}` : '';
  return request(`/api/messages${qs}`);
}

export async function listUsers(): Promise<User[]> {
  return request('/api/users');
}

export async function createUser(body: {
  username: string;
  password: string;
  nickname?: string;
  is_admin?: boolean;
}): Promise<User> {
  return request('/api/users', { method: 'POST', body: JSON.stringify(body) });
}

export async function deleteUser(id: number): Promise<void> {
  return request(`/api/users/${id}`, { method: 'DELETE' });
}

export function openChatSocket(token: string): WebSocket {
  const q = `?token=${encodeURIComponent(token)}`;
  if (API_BASE) {
    const wsBase = API_BASE.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
    return new WebSocket(`${wsBase}/ws${q}`);
  }
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return new WebSocket(`${proto}//${location.host}/ws${q}`);
}

export { ApiError };
