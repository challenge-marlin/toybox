'use client';
import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { apiGet, apiPost, apiDelete } from '../../lib/api';
import { resolveUploadUrl } from '../../lib/assets';
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

// 画像/動画URL解決は共通関数を使用

export default function GlobalFeedPage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [initialized, setInitialized] = useState<boolean>(false);
  const [popularItems, setPopularItems] = useState<FeedItem[]>([]);
  const [popularLoading, setPopularLoading] = useState<boolean>(false);
  const [popularError, setPopularError] = useState<string | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>('');
  const [lightboxType, setLightboxType] = useState<'image' | 'video'>('image');
  const [lightboxAsset, setLightboxAsset] = useState<{
    id: string; type: 'image' | 'video' | 'game' | 'other'; title?: string; authorName?: string; mimeType: string; sizeBytes?: number; fileUrl: string;
  } | null>(null);

  useEffect(() => {
    (async () => {
      const t0 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      setLoading(true);
      try {
        const res = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=24`);
        setItems(Array.isArray(res.items) ? res.items : []);
        setNextCursor(res.nextCursor ?? null);
        const t1 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
        const ms = Math.max(0, t1 - t0);
        try {
          const base = process.env.NEXT_PUBLIC_API_BASE || '';
          const url = base ? `${base}/api/metrics/fevent` : '/api/metrics/fevent';
          const payload = { name: 'feed_load_ms', value: Math.round(ms) } as any;
          navigator.sendBeacon?.(url, new Blob([JSON.stringify(payload)], { type: 'application/json' }))
            || fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), keepalive: true });
        } catch {}
      } catch {
        setItems([]);
        setNextCursor(null);
      } finally {
        setLoading(false);
        setInitialized(true);
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      setPopularLoading(true);
      setPopularError(null);
      try {
        console.log('[PopularFeed] Fetching popular items...');
        const res = await apiGet<{ items: FeedItem[] }>(`/api/feed/popular?limit=12`);
        console.log('[PopularFeed] Response:', res);
        setPopularItems(Array.isArray(res.items) ? res.items : []);
        console.log('[PopularFeed] Items set:', Array.isArray(res.items) ? res.items.length : 0);
      } catch (err) {
        console.error('[PopularFeed] Failed to load popular items:', err);
        const errorMessage = err instanceof Error ? err.message : '人気作品の読み込みに失敗しました';
        console.error('[PopularFeed] Error message:', errorMessage);
        setPopularError(errorMessage);
        setPopularItems([]);
      } finally {
        setPopularLoading(false);
      }
    })();
  }, []);

  async function loadMore() {
    if (!nextCursor || loading) return;
    setLoading(true);
    try {
      const res = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=24&cursor=${encodeURIComponent(nextCursor)}`);
      setItems((prev) => {
        const existingIds = new Set(prev.map((x) => x.id));
        const incoming = Array.isArray(res.items) ? res.items.filter((x) => !existingIds.has(x.id)) : [];
        return [...prev, ...incoming];
      });
      setNextCursor(res.nextCursor ?? null);
    } catch {
      // noop
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!sentinelRef.current) return;
    const el = sentinelRef.current;
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          // 末尾に達したら追加ロード
          if (nextCursor && !loading) {
            void loadMore();
          }
        }
      }
    }, { root: null, rootMargin: '200px', threshold: 0 });
    observer.observe(el);
    return () => { try { observer.disconnect(); } catch {} };
  }, [nextCursor, loading]);

  async function toggleLike(submissionId: string, currentLiked?: boolean, isPopular?: boolean) {
    const updateFn = (prev: FeedItem[]) => prev.map((it) => it.id === submissionId ? { ...it, liked: !currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? -1 : 1)) } : it);
    if (isPopular) {
      setPopularItems(updateFn);
    } else {
      setItems(updateFn);
    }
    try {
      if (currentLiked) {
        await apiDelete<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`);
      } else {
        await apiPost<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`, {} as any);
      }
    } catch {
      const rollbackFn = (prev: FeedItem[]) => prev.map((it) => it.id === submissionId ? { ...it, liked: currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? 1 : -1)) } : it);
      if (isPopular) {
        setPopularItems(rollbackFn);
      } else {
        setItems(rollbackFn);
      }
    }
  }

  function renderFeedItem(s: FeedItem, isPopular?: boolean) {
    return (
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
            onClick={() => { const u = resolveUploadUrl(s.videoUrl); if (u) { setLightboxSrc(u); setLightboxType('video'); setLightboxAsset({ id: s.id, type: 'video', title: s.title || undefined, authorName: s.displayName || s.anonId, mimeType: 'video/mp4', fileUrl: u }); setLightboxOpen(true); } }}
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
            onClick={() => { const u = resolveUploadUrl(s.displayImageUrl || s.imageUrl || null); if (u) { setLightboxSrc(u); setLightboxType('image'); setLightboxAsset({ id: s.id, type: 'image', title: s.title || undefined, authorName: s.displayName || s.anonId, mimeType: 'image/png', fileUrl: u }); setLightboxOpen(true); } }}
          />
        )}
        <div className={`absolute inset-0 pointer-events-none rounded ${s.gameUrl ? 'ring-2 ring-fuchsia-500/70' : (s.videoUrl ? 'ring-2 ring-sky-500/70' : 'ring-2 ring-steam-gold-500/60')} animate-pulse`}></div>
        <button
          onClick={(e) => { e.stopPropagation(); toggleLike(s.id, s.liked, isPopular); }}
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
    );
  }

  return (
    <main className="mx-auto max-w-6xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">みんなの投稿</h1>
      
      {/* 人気作品セクション */}
      <section className="mb-8">
        <h2 className="mb-3 text-xl font-semibold text-steam-gold-300">人気作品</h2>
        {popularLoading ? (
          <div className="text-sm text-steam-iron-300">読み込み中...</div>
        ) : popularError ? (
          <div className="text-sm text-red-400">エラー: {popularError}</div>
        ) : popularItems.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {popularItems.map((s) => renderFeedItem(s, true))}
          </div>
        ) : (
          <div className="text-sm text-steam-iron-300">人気作品はまだありません</div>
        )}
      </section>

      {/* 通常の投稿一覧 */}
      <section>
        <h2 className="mb-3 text-xl font-semibold text-steam-gold-300">最新の投稿</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {items.length === 0 && !loading && <div className="col-span-full text-sm text-steam-iron-300">投稿はまだありません</div>}
          {items.map((s) => renderFeedItem(s, false))}
        </div>
      </section>
      {/* 無限スクロール用の番兵要素 */}
      <div ref={sentinelRef} className="h-1" />

      {/* ロード中表示 */}
      {loading && (
        <div className="mt-4 text-center text-sm text-steam-iron-300">読み込み中…</div>
      )}

      {/* 末端表示（初回ロード済みかつ次カーソル無し） */}
      {initialized && !loading && !nextCursor && items.length > 0 && (
        <div className="mt-4 text-center text-xs text-steam-iron-400">すべて表示しました</div>
      )}
      {/* タイルの詳細リンク（小さく重ねて表示） */}
      <style>{`.feed-card-detail{position:absolute;bottom:6px;left:6px;z-index:10}`}</style>
      <ImageLightbox src={lightboxSrc} alt="submission" open={lightboxOpen} onClose={() => setLightboxOpen(false)} type={lightboxType} asset={lightboxAsset || undefined} />
    </main>
  );
}
