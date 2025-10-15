'use client';
import React, { useState, useEffect } from 'react';
import { getAnonId, setAnonId, generateAnonId } from '../../lib/auth';
import { useRouter } from 'next/navigation';
import { apiPost } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [anonId, setId] = useState('');
  const [identifier, setIdentifier] = useState(''); // email または username
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setId('');
  }, []);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    // 匿名ログインは廃止
  }

  async function onLoginAccount(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setError(null);
    try {
      const body: any = { password };
      if (identifier.includes('@')) body.email = identifier; else body.username = identifier;
      const res = await apiPost<{ ok: boolean }>(`/api/auth/login`, body);
      if (res?.ok) {
        setMsg('ログインしました');
        try { localStorage.setItem('toybox_mypage_force_reload', '1'); } catch {}
        router.push('/mypage');
      }
    } catch (e: any) {
      setError(e?.message || 'ログインに失敗しました');
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">ログイン</h1>
      {msg && <div className="mb-3 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-gold-300">{msg}</div>}
      {error && <div className="mb-3 rounded border border-red-700 bg-red-900 p-2 text-sm text-red-200">{error}</div>}

      <p className="mb-3 text-steam-gold-300 font-semibold">アカウントでログイン</p>
      <form onSubmit={onLoginAccount} className="space-y-3 mb-8">
        <div>
          <label className="block text-sm text-steam-gold-300">メールまたはユーザーID</label>
          <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" />
        </div>
        <div>
          <label className="block text-sm text-steam-gold-300">パスワード</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" />
        </div>
        <button className="rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400">ログイン</button>
      </form>

      {/* 匿名ログインは廃止 */}
    </main>
  );
}


