'use client';
import React, { useState, useEffect } from 'react';
import { getAnonId, setAnonId, generateAnonId } from '../../lib/auth';
import { useRouter } from 'next/navigation';
import { apiPost } from '../../lib/api';

interface PenaltyInfo {
  type: 'WARNING' | 'SUSPEND' | 'BAN';
  message: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [anonId, setId] = useState('');
  const [identifier, setIdentifier] = useState(''); // email または username
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [penalty, setPenalty] = useState<PenaltyInfo | null>(null);

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
    setPenalty(null);
    try {
      const body: any = { password };
      if (identifier.includes('@')) body.email = identifier; else body.username = identifier;
      const res = await apiPost<{ ok: boolean; penalty?: PenaltyInfo }>(`/api/auth/login`, body);
      if (res?.ok) {
        // 警告メッセージがある場合は表示
        if (res.penalty && res.penalty.message) {
          setPenalty(res.penalty);
        } else {
          setMsg('ログインしました');
          try { localStorage.setItem('toybox_mypage_force_reload', '1'); } catch {}
          router.push('/mypage');
        }
      }
    } catch (e: any) {
      setError(e?.message || 'ログインに失敗しました');
    }
  }
  
  function handlePenaltyClose() {
    const penaltyType = penalty?.type;
    setPenalty(null);
    
    // タイプに応じて異なる処理
    if (penaltyType === 'WARNING') {
      // 警告の場合はマイページにリダイレクト
      setMsg('ログインしました');
      try { localStorage.setItem('toybox_mypage_force_reload', '1'); } catch {}
      router.push('/mypage');
    } else if (penaltyType === 'SUSPEND' || penaltyType === 'BAN') {
      // アカウント停止またはBANの場合はトークンを削除してログインページに戻る
      try {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      } catch {}
      
      if (penaltyType === 'SUSPEND') {
        setError('アカウントが停止されています。ログインページに戻ります。');
      } else {
        setError('アカウントが削除されました。ログインページに戻ります。');
      }
      
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">ログイン</h1>
      {msg && <div className="mb-3 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-gold-300">{msg}</div>}
      {error && <div className="mb-3 rounded border border-red-700 bg-red-900 p-2 text-sm text-red-200">{error}</div>}
      
      {/* 警告メッセージモーダル */}
      {penalty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70">
          <div className="mx-4 max-w-2xl rounded-lg border-2 bg-steam-iron-900 p-6 shadow-lg" style={{
            borderColor: penalty.type === 'WARNING' ? '#fbbf24' : penalty.type === 'SUSPEND' ? '#f59e0b' : '#dc2626'
          }}>
            <div className="mb-4 flex items-center gap-2 text-xl font-semibold" style={{
              color: penalty.type === 'WARNING' ? '#fbbf24' : penalty.type === 'SUSPEND' ? '#f59e0b' : '#dc2626'
            }}>
              {penalty.type === 'WARNING' && '⚠️ 警告'}
              {penalty.type === 'SUSPEND' && '⛔ アカウント停止'}
              {penalty.type === 'BAN' && '🚫 BAN（アカウント削除）'}
            </div>
            <div className="mb-6 whitespace-pre-wrap text-steam-iron-100 leading-relaxed">
              {penalty.message}
            </div>
            <div className="flex justify-end">
              <button
                onClick={handlePenaltyClose}
                className="rounded bg-steam-gold-500 px-6 py-2 text-black font-medium hover:bg-steam-gold-400"
              >
                了解しました
              </button>
            </div>
          </div>
        </div>
      )}

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


