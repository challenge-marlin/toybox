function getApiBase(): string {
  const isServer = typeof window === 'undefined';
  if (isServer) {
    return process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:4000';
  }
  return process.env.NEXT_PUBLIC_API_BASE || '';
}

function joinUrl(base: string, path: string): string {
  const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export async function apiGet<T>(path: string, opts?: { anonId?: string; signal?: AbortSignal }): Promise<T> {
  const url = joinUrl(getApiBase(), path);
  const headers: Record<string, string> = { 'Accept': 'application/json' };
  if (opts?.anonId) headers['x-anon-id'] = opts.anonId;
  const res = await fetch(url, { headers, signal: opts?.signal, cache: 'no-store', credentials: 'include' });
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json();
      if (errorData.error) {
        errorMessage = errorData.error;
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // JSON parse failed, use default message
    }
    if (res.status === 401) {
      throw new Error('ログイン情報の有効期限が切れました。再ログインしてください。');
    }
    if (res.status === 403) {
      throw new Error(errorMessage || 'アクセスが拒否されました');
    }
    throw new Error(errorMessage);
  }
  return (await res.json()) as T;
}

export async function apiPost<T, B = unknown>(path: string, body: B, opts?: { anonId?: string; signal?: AbortSignal }): Promise<T> {
  const url = joinUrl(getApiBase(), path);
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  if (opts?.anonId) headers['x-anon-id'] = opts.anonId;
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal: opts?.signal,
    credentials: 'include'
  });
  if (!res.ok) {
    if (res.status === 401) throw new Error('ログイン情報の有効期限が切れました。再ログインしてください。');
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function apiPatch<T, B = unknown>(path: string, body: B, opts?: { anonId?: string; signal?: AbortSignal }): Promise<T> {
  const url = joinUrl(getApiBase(), path);
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  if (opts?.anonId) headers['x-anon-id'] = opts.anonId;
  const res = await fetch(url, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(body),
    signal: opts?.signal,
    credentials: 'include'
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as T;
}

export async function apiUpload<T>(path: string, file: File, opts?: { anonId?: string; signal?: AbortSignal }): Promise<T> {
  const url = joinUrl(getApiBase(), path);
  const form = new FormData();
  form.append('file', file);
  const headers: Record<string, string> = { 'Accept': 'application/json' };
  if (opts?.anonId) headers['x-anon-id'] = opts.anonId;
  const res = await fetch(url, { method: 'POST', headers, body: form, signal: opts?.signal, credentials: 'include' });
  if (!res.ok) {
    if (res.status === 401) throw new Error('ログイン情報の有効期限が切れました。再ログインしてください。');
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function apiDelete<T>(path: string, opts?: { anonId?: string; signal?: AbortSignal }): Promise<T> {
  const url = joinUrl(getApiBase(), path);
  const headers: Record<string, string> = { 'Accept': 'application/json' };
  if (opts?.anonId) headers['x-anon-id'] = opts.anonId;
  const res = await fetch(url, { method: 'DELETE', headers, signal: opts?.signal, credentials: 'include' });
  if (!res.ok) {
    if (res.status === 401) throw new Error('ログイン情報の有効期限が切れました。再ログインしてください。');
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}