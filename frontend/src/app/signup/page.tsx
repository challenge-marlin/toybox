"use client";
import React, { useState } from 'react';
import { apiPost } from '../../lib/api';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setError(null);
    setLoading(true);
    try {
      const body: any = { username, displayName, password };
      const res = await apiPost<{ ok: boolean }>(`/api/auth/register`, body);
      if (res?.ok) {
        setMsg('アカウントを作成しました。マイページへ移動します…');
        try { localStorage.setItem('toybox_mypage_force_reload', '1'); } catch {}
        router.push('/mypage');
      }
    } catch (e: any) {
      setError(e?.message || '登録に失敗しました');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">アカウント作成</h1>
      {msg && <div className="mb-3 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-gold-300">{msg}</div>}
      {error && <div className="mb-3 rounded border border-red-700 bg-red-900 p-2 text-sm text-red-200">{error}</div>}
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-steam-gold-300">ユーザーID（英数_ 3-30文字）</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" />
        </div>
        <div>
          <label className="block text-sm text-steam-gold-300">表示名</label>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="w-full rounded border border-steAM-iron-700 bg-steam-iron-900 p-2" />
        </div>
        <div>
          <label className="block text-sm text-steam-gold-300">パスワード</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" />
        </div>
        <button disabled={loading} className="w-full rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400 disabled:opacity-60">{loading ? '作成中…' : '作成'}</button>
      </form>
    </main>
  );
}


