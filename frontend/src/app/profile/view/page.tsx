"use client";
import React, { useEffect, useState } from 'react';
import { API_BASE, apiGet, apiPost, apiDelete } from '../../../lib/api';
import { resolveUploadUrl } from '../../../lib/assets';
import TitleDisplay from '../../../components/TitleDisplay';
import ImageLightbox from '../../../components/ImageLightbox';
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

type Submission = { id: string; imageUrl?: string | null; videoUrl?: string | null; gameUrl?: string | null; displayImageUrl?: string | null; createdAt: string; likesCount?: number; liked?: boolean };

// 画像/動画URL解決は共通関数を使用

export default function ProfileViewPage() {
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [items, setItems] = useState<Submission[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>('');
  const [lightboxType, setLightboxType] = useState<'image' | 'video'>('image');
  const [lightboxAsset, setLightboxAsset] = useState<{ id: string; type: 'image' | 'video' | 'game' | 'other'; title?: string; authorName?: string; mimeType: string; sizeBytes?: number; fileUrl: string } | null>(null);

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
      } catch { /* noop */ }

      // 自分の提出一覧
      try {
        const s = await apiGet<{ items: Submission[]; nextCursor: string | null }>(`/api/user/submissions/${encodeURIComponent(a)}?limit=12`);
        setItems(s.items);
        setNextCursor(s.nextCursor ?? null);
      } catch { setItems([]); setNextCursor(null); }
    })();
  }, []);

  async function loadMore() {
    if (!nextCursor || !profile?.anonId) return;
    try {
      const s = await apiGet<{ items: Submission[]; nextCursor: string | null }>(`/api/user/submissions/${encodeURIComponent(profile.anonId)}?limit=12&cursor=${encodeURIComponent(nextCursor)}`);
      setItems((prev) => [...prev, ...s.items]);
      setNextCursor(s.nextCursor ?? null);
    } catch {}
  }

  async function toggleLike(submissionId: string, currentLiked?: boolean) {
    setItems((prev) => prev.map((it) => it.id === submissionId ? { ...it, liked: !currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? -1 : 1)) } : it));
    try {
      if (currentLiked) {
        await apiDelete<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`);
      } else {
        await apiPost<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`, {} as any);
      }
    } catch {
      setItems((prev) => prev.map((it) => it.id === submissionId ? { ...it, liked: currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? 1 : -1)) } : it));
    }
  }

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

        <h2 className="mt-6 mb-3 text-steam-gold-300 font-semibold">提出一覧</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {items.length === 0 && (
            <div className="text-sm text-steam-iron-300">提出はまだありません</div>
          )}
          {items.map((s) => (
            <div
              key={s.id}
              className={`relative rounded border ${s.gameUrl ? 'border-fuchsia-500' : (s.videoUrl ? 'border-sky-500' : 'border-steam-iron-700')} bg-steam-iron-900 group`}
            >
              {s.gameUrl ? (
                <div className="w-full aspect-square flex items-center justify-center p-3 select-none">
                  <div className="flex flex-col items-center justify-center text-steam-iron-200">
                    <svg aria-hidden="true" width="40" height="40" viewBox="0 0 24 24" className="text-steam-gold-300 mb-1" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c0 .69.28 1.32.73 1.77.45.45 1.08.73 1.77.73H21a2 2 0 1 1 0 4h-.09c-.69 0-1.32.28-1.77.73-.45.45-.73 1.08-.73 1.77z"/>
                    </svg>
                    <div className="text-xs tracking-widest font-semibold">GAME</div>
                  </div>
                </div>
              ) : s.videoUrl ? (
                <div
                  className="w-full aspect-square flex items-center justify-center p-3 cursor-pointer"
                  onClick={() => { const u = resolveUploadUrl(s.videoUrl); if (u) { setLightboxSrc(u); setLightboxType('video'); setLightboxAsset({ id: s.id, type: 'video', title: undefined, authorName: profile?.displayName || profile?.anonId, mimeType: 'video/mp4', fileUrl: u }); setLightboxOpen(true); } }}
                >
                  <video
                    src={resolveUploadUrl(s.displayImageUrl || s.videoUrl)}
                    className="max-h-full max-w-full object-contain rounded"
                    muted
                    preload="metadata"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-12 w-12 rounded-full bg-black/60 text-white flex items-center justify-center shadow-lg">
                      <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>
                </div>
              ) : (
                <img
                  loading="lazy"
                  src={resolveUploadUrl(s.displayImageUrl || s.imageUrl || null)}
                  alt="submission"
                  className="w-full aspect-square object-contain p-2 cursor-zoom-in"
                  onClick={() => { const u = resolveUploadUrl(s.displayImageUrl || s.imageUrl || null); if (u) { setLightboxSrc(u); setLightboxType('image'); setLightboxAsset({ id: s.id, type: 'image', title: undefined, authorName: profile?.displayName || profile?.anonId, mimeType: 'image/png', fileUrl: u }); setLightboxOpen(true); } }}
                />
              )}
              <div className={`absolute inset-0 pointer-events-none rounded ${s.gameUrl ? 'ring-2 ring-fuchsia-500/70' : (s.videoUrl ? 'ring-2 ring-sky-500/70' : 'ring-2 ring-steam-gold-500/60')} animate-pulse`}></div>
              <button
                onClick={(e) => { e.stopPropagation(); toggleLike(s.id, s.liked); }}
                className="absolute bottom-2 right-2 z-10 inline-flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white hover:bg-black/80"
                aria-label="いいね"
              >
                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill={s.liked ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" className={s.liked ? 'text-rose-400' : 'text-steam-iron-200'}>
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
                <span>{s.likesCount ?? 0}</span>
              </button>
              {s.gameUrl && (
                <a
                  href={resolveUploadUrl(s.gameUrl) || '#'}
                  target="_blank"
                  rel="noreferrer"
                  className="absolute top-2 left-2 z-10 inline-flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white hover:bg:black/80"
                  title="ゲームを開く"
                  onClick={(e) => e.stopPropagation()}
                >
                  <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l-.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c0 .69.28 1.32.73 1.77.45.45 1.08.73 1.77.73H21a2 2 0 1 1 0 4h-.09c-.69 0-1.32.28-1.77.73-.45.45-.73 1.08-.73 1.77z"/>
                </svg>
                開く
              </a>
            )}
          </div>
        ))}
      </div>
      {nextCursor && (
        <button onClick={loadMore} className="mt-4 rounded bg-steam-iron-800 px-3 py-1 text-steam-gold-300 hover:bg-steam-iron-700">さらに読み込む</button>
      )}
      <ImageLightbox src={lightboxSrc} alt="submission" open={lightboxOpen} onClose={() => setLightboxOpen(false)} type={lightboxType} asset={lightboxAsset || undefined} />
    </main>
  </>
  );
}
