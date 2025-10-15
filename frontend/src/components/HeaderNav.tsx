'use client';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiGet, apiPost } from '../lib/api';

export default function HeaderNav() {
  const router = useRouter();
  const [anonId, setId] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  useEffect(() => {
    (async () => {
      try {
        const me = await apiGet<{ ok: boolean; user: { anonId: string; displayName?: string } | null }>(`/api/auth/me`);
        setId(me.ok && me.user ? me.user.anonId : null);
        setDisplayName(me.ok && me.user ? (me.user.displayName || null) : null);
      } catch {
        setId(null);
        setDisplayName(null);
      }
    })();
  }, []);

  async function onLogout() {
    try { await apiPost(`/api/auth/logout`, {} as any); } catch {}
    setId(null);
    setDisplayName(null);
    try { router.push('/'); } catch {}
  }

  // 匿名IDは廃止

  return (
    <header className="border-b border-steam-iron-800 bg-steam-iron-900/70">
      <div className="mx-auto flex max-w-6xl items-center justify-between p-3 text-sm">
        <nav className="flex items-center gap-4">
          <Link href="/">
            <img src="/hero/toybox-title.png" alt="ToyBox" className="h-8 md:h-10 w-auto" />
          </Link>
          {anonId ? (
            <>
              <Link href="/mypage" className="text-steam-gold-400 hover:underline">マイページ</Link>
              <Link href="/collection" className="text-steam-gold-400 hover:underline">コレクション</Link>
              <Link href={`/profile/view`} className="text-steam-gold-400 hover:underline">プロフィール</Link>
            </>
          ) : (
            <>
              {/* 未ログイン時はコレクションはログイン誘導 */}
              <Link href={"/login?next=/collection"} className="text-steam-gold-400 hover:underline">コレクション</Link>
              <Link href="/login" className="text-steam-gold-400 hover:underline">ログイン</Link>
            </>
          )}
        </nav>
        <div className="flex items-center gap-3 text-steam-iron-200">
          {anonId ? (
            <>
              <span className="hidden md:inline">{displayName || anonId}</span>
              <button onClick={onLogout} className="rounded bg-steam-brown-600 px-2 py-1 text-white hover:bg-steam-brown-700">ログアウト</button>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}


