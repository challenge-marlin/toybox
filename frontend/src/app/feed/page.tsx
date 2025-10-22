'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { API_BASE, apiGet, apiPost, apiDelete } from '../../lib/api';
import ImageLightbox from '../../components/ImageLightbox';

type FeedItem = {
  id: string;
  anonId: string;
  displayName?: string | null;
  createdAt: string;
  imageUrl?: string | null;
  videoUrl?: string | null;
  avatarUrl?: string | null;
  displayImageUrl?: string | null;
  title?: string | null;
  gameUrl?: string | null;
  likesCount?: number;
  liked?: boolean;
};

function resolveUploadUrl(u?: string | null): string | undefined {
  if (!u) return undefined;
  if (u.startsWith('/uploads/')) return `${API_BASE}${u}`;
  return u;
}

export default function GlobalFeedPage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>('');
  const [lightboxType, setLightboxType] = useState<'image' | 'video'>('image');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=24`);
        setItems(res.items);
        setNextCursor(res.nextCursor ?? null);
      } catch {
        setItems([]);
        setNextCursor(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function loadMore() {
    if (!nextCursor || loading) return;
    setLoading(true);
    try {
      const res = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=24&cursor=${encodeURIComponent(nextCursor)}`);
      setItems((prev) => [...prev, ...res.items]);
      setNextCursor(res.nextCursor ?? null);
    } catch {
      // noop
    } finally {
      setLoading(false);
    }
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
    <main className="mx-auto max-w-6xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">みんなの投稿</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {items.length === 0 && !loading && <div className="col-span-full text-sm text-steam-iron-300">投稿はまだありません</div>}
        {items.map((s) => (
          <div
            key={s.id}
            className={`relative rounded border ${s.gameUrl ? 'border-fuchsia-500' : (s.videoUrl ? 'border-sky-500' : 'border-steam-iron-700')} bg-steam-iron-900 group`}
          >
            <div className="absolute top-2 left-2 z-10 text-[10px] px-2 py-0.5 rounded bg-black/60 text-white">
              <Link href={`/${encodeURIComponent(s.anonId)}`} className="hover:underline">{s.displayName || s.anonId}</Link>
            </div>
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
                onClick={() => { const u = resolveUploadUrl(s.videoUrl); if (u) { setLightboxSrc(u); setLightboxType('video'); setLightboxOpen(true); } }}
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
                className="w-full aspect-square object-contain p-3 cursor-zoom-in"
                onClick={() => { const u = resolveUploadUrl(s.displayImageUrl || s.imageUrl || null); if (u) { setLightboxSrc(u); setLightboxType('image'); setLightboxOpen(true); } }}
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
                className="absolute top-2 right-2 z-10 inline-flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white hover:bg:black/80"
                title="ゲームを開く"
                onClick={(e) => e.stopPropagation()}
              >
                <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c0 .69.28 1.32.73 1.77.45.45 1.08.73 1.77.73H21a2 2 0 1 1 0 4h-.09c-.69 0-1.32.28-1.77.73-.45.45-.73 1.08-.73 1.77z"/>
                </svg>
                開く
              </a>
            )}
          </div>
        ))}
      </div>
      {nextCursor && (
        <div className="mt-4">
          <button onClick={loadMore} disabled={loading} className="rounded bg-steam-iron-800 px-3 py-1 text-steam-gold-300 hover:bg-steam-iron-700 disabled:opacity-60">さらに読み込む</button>
        </div>
      )}
      <ImageLightbox src={lightboxSrc} alt="submission" open={lightboxOpen} onClose={() => setLightboxOpen(false)} type={lightboxType} />
    </main>
  );
}
