'use client';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { apiGet, apiPost } from '../lib/api';

export default function HeaderNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [anonId, setId] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifUnread, setNotifUnread] = useState<number>(0);
  const [notifItems, setNotifItems] = useState<{ type: 'like'; fromAnonId: string; submissionId: string; message: string; createdAt: string; read?: boolean }[]>([]);
  const [notifNextOffset, setNotifNextOffset] = useState<number | null>(null);
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

  useEffect(() => {
    if (!anonId) return;
    (async () => {
      try {
        const res = await apiGet<{ items: any[]; unread: number; nextOffset: number | null }>(`/api/notifications?limit=10`);
        setNotifItems(res.items);
        setNotifUnread(res.unread);
        setNotifNextOffset(res.nextOffset);
      } catch {
        setNotifItems([]); setNotifUnread(0); setNotifNextOffset(null);
      }
    })();
  }, [anonId]);

  async function loadMoreNotifs() {
    if (notifNextOffset == null) return;
    try {
      const res = await apiGet<{ items: any[]; unread: number; nextOffset: number | null }>(`/api/notifications?limit=10&offset=${notifNextOffset}`);
      setNotifItems((prev) => [...prev, ...res.items]);
      setNotifUnread(res.unread);
      setNotifNextOffset(res.nextOffset);
    } catch {}
  }

  async function onToggleNotif() {
    setNotifOpen((o) => !o);
    try {
      // 開いた直後に既読化（サーバ側で全件既読処理）
      const nextOpen = !notifOpen;
      if (nextOpen && notifUnread > 0) {
        await apiPost(`/api/notifications/read`, {} as any);
        setNotifUnread(0);
        setNotifItems((prev) => prev.map((n) => ({ ...n, read: true })));
      }
    } catch {}
  }

  async function onLogout() {
    try { await apiPost(`/api/auth/logout`, {} as any); } catch {}
    setId(null);
    setDisplayName(null);
    try { router.push('/'); } catch {}
  }

  // 匿名IDは廃止
  const simpleHeader = pathname?.startsWith('/login') || pathname?.startsWith('/signup');

  return (
    <header className="border-b border-steam-iron-800 bg-steam-iron-900/70">
      <div className="mx-auto flex max-w-6xl items-center justify-between p-3 text-sm">
        <nav className="flex items-center gap-4">
          <Link href={anonId ? "/mypage" : "/"}>
            <img src="/hero/toybox-title.png" alt="ToyBox" className="h-8 md:h-10 w-auto" />
          </Link>
          {!simpleHeader && (
            anonId ? (
              <>
                <Link href="/mypage" className="text-steam-gold-400 hover:underline">マイページ</Link>
                <Link href="/collection" className="text-steam-gold-400 hover:underline">コレクション</Link>
                <Link href={`/profile/view`} className="text-steam-gold-400 hover:underline">プロフィール</Link>
                <Link href="/feed" className="text-steam-gold-400 hover:underline">みんなの投稿</Link>
              </>
            ) : (
              <>
                {/* 未ログイン時はコレクションはログイン誘導 */}
                <Link href={"/login?next=/collection"} className="text-steam-gold-400 hover:underline">コレクション</Link>
                <Link href="/login" className="text-steam-gold-400 hover:underline">ログイン</Link>
                <Link href="/feed" className="text-steam-gold-400 hover:underline">みんなの投稿</Link>
              </>
            )
          )}
        </nav>
        {!simpleHeader && (
          <div className="flex items-center gap-3 text-steam-iron-200">
            {anonId ? (
              <>
                <div className="relative">
                  <button
                    onClick={onToggleNotif}
                    className="relative rounded px-2 py-1 hover:bg-steam-iron-800"
                    aria-label="通知"
                  >
                    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-steam-gold-300">
                      <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                      <path d="M13.73 21a2 2 0 01-3.46 0" />
                    </svg>
                    {notifUnread > 0 && (
                      <span className="absolute -top-1 -right-1 rounded-full bg-red-600 text-white text-[10px] px-1">{notifUnread}</span>
                    )}
                  </button>
                  {notifOpen && (
                    <div className="absolute right-0 mt-2 w-72 rounded border border-steam-iron-700 bg-steam-iron-900 shadow-xl z-50">
                      <div className="max-h-80 overflow-auto divide-y divide-steam-iron-800">
                        {notifItems.length === 0 && (
                          <div className="p-3 text-xs text-steam-iron-300">通知はありません</div>
                        )}
                        {notifItems.map((n, i) => (
                          <div key={i} className="p-3 text-xs text-steam-iron-100">
                            <div className="font-semibold text-steam-gold-300">{n.message}</div>
                            <div className="text-[10px] text-steam-iron-300">{new Date(n.createdAt).toLocaleString()}</div>
                          </div>
                        ))}
                      </div>
                      <div className="p-2 text-right">
                        {notifNextOffset != null ? (
                          <button onClick={loadMoreNotifs} className="text-[11px] text-steam-gold-300 hover:underline">もっと見る</button>
                        ) : (
                          <span className="text-[11px] text-steam-iron-300">すべて表示</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                <span className="hidden md:inline">{displayName || anonId}</span>
                <button onClick={onLogout} className="rounded bg-steam-brown-600 px-2 py-1 text-white hover:bg-steam-brown-700">ログアウト</button>
              </>
            ) : null}
          </div>
        )}
      </div>
    </header>
  );
}


