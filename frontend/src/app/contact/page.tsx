'use client';
import React, { useState } from 'react';
// APIは同一オリジンの相対パスで呼び出します

export default function ContactPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (sending) return;
    setError(null);
    setSending(true);
    try {
      const res = await fetch(`/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, email, message })
      });
      if (!res.ok) {
        let msg = '送信に失敗しました';
        try {
          const ct = res.headers.get('Content-Type') || '';
          if (ct.includes('application/json')) {
            const j = await res.json();
            msg = j?.error || msg;
          } else {
            msg = await res.text();
          }
        } catch {}
        throw new Error(msg);
      }
      setDone(true);
      setName(''); setEmail(''); setMessage('');
    } catch (err: any) {
      setError(err?.message || '送信に失敗しました');
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">お問い合わせ</h1>
      <p className="text-sm text-steam-iron-200 mb-4">ご意見やご質問、不適切コンテンツの通報はこちらからお送りください。</p>
      {done && (
        <div className="mb-4 rounded border border-green-700 bg-green-900/40 text-green-200 px-3 py-2">送信しました。ご連絡ありがとうございます。</div>
      )}
      {error && (
        <div className="mb-4 rounded border border-red-700 bg-red-900/40 text-red-200 px-3 py-2">{error}</div>
      )}
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="block text-sm text-steam-iron-200 mb-1">お名前（必須）</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm text-steam-iron-200 mb-1">メールアドレス（任意）</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm text-steam-iron-200 mb-1">お問い合わせ内容</label>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 px-3 py-2 min-h-[160px]" required />
        </div>
        <div>
          <button disabled={sending || name.trim().length === 0 || message.trim().length < 5} className="rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600 disabled:opacity-50">{sending ? '送信中…' : '送信'}</button>
        </div>
      </form>
    </main>
  );
}


