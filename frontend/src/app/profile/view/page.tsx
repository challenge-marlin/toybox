"use client";
import React, { useEffect, useState } from 'react';
import { API_BASE, apiGet } from '../../../lib/api';
import TitleDisplay from '../../../components/TitleDisplay';
const FRAME_URL = '/uploads/cards/frame.png';
// 匿名IDは廃止。/api/auth/me から取得

type PublicProfile = {
  anonId: string;
  displayName?: string | null;
  avatarUrl?: string | null;
  headerUrl?: string | null;
  bio?: string | null;
  activeTitle?: string | null;
  activeTitleUntil?: string | null;
  cardsAlbum?: { id: string; obtainedAt?: string }[];
};

type CardEntry = { id: string; obtainedAt?: string };

function resolveUploadUrl(u?: string | null): string | undefined {
  if (!u) return undefined;
  if (u.startsWith('/uploads/')) return `${API_BASE}${u}`;
  return u;
}

export default function ProfileViewPage() {
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [cards, setCards] = useState<CardEntry[]>([]);

  useEffect(() => {
    (async () => {
      let a: string | null = null;
      try {
        const me = await apiGet<{ ok: boolean; user: { anonId: string } | null }>(`/api/auth/me`);
        a = me.ok && me.user ? me.user.anonId : null;
      } catch {}
      if (!a) { window.location.href = '/login?next=/profile/view'; return; }
      try {
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(a)}`);
        setProfile(p);
        setCards(p.cardsAlbum || []);
      } catch { /* noop */ }
    })();
  }, []);

  return (
    <>
      {/* Full-width header directly under global nav */}
      <section className="w-full bg-steam-iron-800">
        <div className="h-48 md:h-56 lg:h-64 w-full">
          {resolveUploadUrl(profile?.headerUrl) ? (
            <img src={resolveUploadUrl(profile?.headerUrl)} alt="header" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">NO Image</div>
          )}
        </div>
      </section>

      <main className="mx-auto max-w-4xl p-4">
        {/* Overlapped avatar under the header */}
        <div className="-mt-16 md:-mt-20 flex justify-start">
          <div className="h-[200px] w-[200px] overflow-hidden rounded-full border-4 border-steam-iron-900 ring-2 ring-steam-iron-700 bg-steam-iron-800">
            {resolveUploadUrl(profile?.avatarUrl) ? (
              <img src={resolveUploadUrl(profile?.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">未設定</div>
            )}
          </div>
        </div>

        {/* Name and ID */}
        <div className="mt-3 text-left">
          <div className="text-lg font-semibold text-steam-iron-100">{profile?.displayName || '—'}</div>
          <div className="text-xs text-steam-iron-300">{profile?.anonId || ''}</div>
          {profile?.activeTitle && (
            <div className="mt-3">
              <TitleDisplay titleText={profile.activeTitle} rank="BRONZE" rarity="N" />
            </div>
          )}
        </div>

        {/* Bio under avatar */}
        {profile?.bio && (
          <div className="mt-4 text-left text-sm leading-relaxed text-steam-iron-200 whitespace-pre-wrap">
            {profile.bio}
          </div>
        )}

        <h2 className="mt-6 mb-3 text-steam-gold-300 font-semibold">所持カード</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {cards.length === 0 && (
            <div className="text-sm text-steam-iron-300">カードはまだありません</div>
          )}
          {cards.map((c) => (
            <div key={c.id} className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
              <div className="relative aspect-[2/3] bg-steam-iron-800 rounded mb-2 overflow-hidden">
                <CardImageById cardId={c.id} />
                <img src={FRAME_URL} alt="" aria-hidden="true" className="absolute inset-0 w-full h-full object-contain pointer-events-none" />
              </div>
              <div className="text-sm text-steam-gold-200 text-center">{c.id}</div>
              {c.obtainedAt && (
                <div className="mt-1 text-[11px] text-steam-iron-300 text-center">{new Date(c.obtainedAt).toLocaleDateString()}</div>
              )}
            </div>
          ))}
        </div>
      </main>
    </>
  );
}

function CardImageById({ cardId }: { cardId: string }) {
  const srcs = candidatesForId(cardId);
  const [idx, setIdx] = React.useState(0);
  if (srcs.length === 0) return null;
  const src = srcs[Math.min(idx, srcs.length - 1)];
  return (
    <img
      src={src}
      alt={cardId}
      className="absolute inset-0 w-full h-full object-contain"
      style={{ transform: 'scale(0.97)', transformOrigin: 'center' }}
      onError={() => setIdx((i) => Math.min(i + 1, srcs.length - 1))}
    />
  );
}

function candidatesForId(cardId: string): string[] {
  const xs: string[] = [];
  // 文字ID（C001/E001）
  xs.push(`${API_BASE}/uploads/cards/${cardId}.png`);
  // 数値ID（Character=C### -> ###, Effect=E### -> 100+###）
  const m = cardId.match(/^[CE](\d{1,3})$/i);
  if (m) {
    const n = parseInt(m[1], 10);
    const isEffect = /^E/i.test(cardId);
    const mapped = isEffect ? 100 + n : n;
    xs.push(`${API_BASE}/uploads/cards/${mapped}.png`);
  }
  return Array.from(new Set(xs));
}


