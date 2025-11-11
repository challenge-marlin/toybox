'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
// 匿名IDは廃止。必要時は /api/auth/me から取得
import { apiGet, apiPost, apiDelete } from '../../lib/api';
import { resolveUploadUrl } from '../../lib/assets';
import CardReveal from '../../components/CardReveal';
import ImageLightbox from '../../components/ImageLightbox';
import { useToast } from '../../components/ToastProvider';

type Submission = { id: string; imageUrl?: string; displayImageUrl?: string; createdAt: string; gameUrl?: string | null; videoUrl?: string | null; likesCount?: number; liked?: boolean };
type FeedItem = { id: string; anonId: string; displayName?: string | null; imageUrl: string; avatarUrl?: string | null; displayImageUrl?: string; createdAt: string; title?: string | null };
  type PublicProfile = { anonId: string; displayName?: string | null; avatarUrl?: string | null; bio?: string | null; updatedAt?: string | null };

type SubmitResult = {
  jpResult: 'none';
  probability: number;
  bonusCount: number;
  rewardTitle?: string;
  rewardCardId?: string;
  rewardCard?: { card_id: string; card_name: string; rarity?: 'SSR' | 'SR' | 'R' | 'N'; image_url?: string | null };
  jackpotRecordedAt?: string | null;
};

export default function MyPage() {
  const toast = useToast();
  const [anonId, setAnonId] = useState<string | null>(null);
  const [topicWork, setTopicWork] = useState<string>('');
  const [topicPlay, setTopicPlay] = useState<string>('');
  const [topicWorkVisible, setTopicWorkVisible] = useState<boolean>(false);
  const [topicPlayVisible, setTopicPlayVisible] = useState<boolean>(false);
  const [titleBadge, setTitleBadge] = useState<string | null>(null);
  const [titleUntil, setTitleUntil] = useState<string | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const FEED_MAX_ITEMS = 100;
  const [submitters, setSubmitters] = useState<{ anonId: string; displayName?: string | null }[]>([]);
  const [ranking, setRanking] = useState<{ anonId: string; displayName?: string | null; count: number }[]>([]);
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // 提出後の演出オーバーレイ
  const [flowOpen, setFlowOpen] = useState(false);
  const [flowPhase, setFlowPhase] = useState<'idle'|'card'|'title'|'done'>('idle');
  const [flowResult, setFlowResult] = useState<SubmitResult | null>(null);
  const [fadeOut, setFadeOut] = useState(false);
  const [cardReveal, setCardReveal] = useState<{ imageUrl?: string | null; cardName: string; rarity?: 'SSR' | 'SR' | 'R' | 'N' } | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>('');
  const [lightboxType, setLightboxType] = useState<'image' | 'video'>('image');
  const [lightboxAsset, setLightboxAsset] = useState<{ id: string; type: 'image' | 'video' | 'game' | 'other'; title?: string; authorName?: string; mimeType: string; sizeBytes?: number; fileUrl: string } | null>(null);
  const [pendingFlow, setPendingFlow] = useState<SubmitResult | null>(null);
  const [okLoading, setOkLoading] = useState(false);

  function localKey(a: string) {
    return `toybox_local_submissions_${a}`;
  }

  function loadLocalSubmissions(a: string): Submission[] {
    try {
      const raw = localStorage.getItem(localKey(a));
      if (!raw) return [];
      const parsed = JSON.parse(raw) as Submission[];
      if (!Array.isArray(parsed)) return [];
      return parsed;
    } catch {
      return [];
    }
  }

  function saveLocalSubmissions(a: string, items: Submission[]) {
    try {
      localStorage.setItem(localKey(a), JSON.stringify(items));
    } catch {}
  }

  async function onUploadFile(file: File) {
    if (!anonId) return;
    if (uploading) return; // 二重起動防止
    setUploadError(null);
    toast.info('アップロードを開始しました');
    setUploading(true);
    const startedAt = Date.now();
    try {
      // PNG/JPEG/MP4/WEBM/OGG を許可
      const isJpeg = file.type === 'image/jpeg' || /\.(jpe?g)$/i.test(file.name);
      const isPng = file.type === 'image/png' || /\.(png)$/i.test(file.name);
      const isMp4 = file.type === 'video/mp4' || /\.(mp4)$/i.test(file.name);
      const isWebm = file.type === 'video/webm' || /\.(webm)$/i.test(file.name);
      const isOgg = file.type === 'video/ogg' || /\.(ogg)$/i.test(file.name);
      const isVideo = isMp4 || isWebm || isOgg;
      if (!(isJpeg || isPng || isVideo)) {
        throw new Error('PNG / JPEG / MP4 / WEBM / OGG のみ対応しています');
      }
      // 1GB 制限（サーバ設定に合わせる）
      if (file.size > 1024 * 1024 * 1024) {
        throw new Error('ファイルサイズが大きすぎます（最大1GB）');
      }
      // 1) 先にサーバへアップロードし、相対URLを取得
      const form = new FormData();
      form.append('file', file);
      const uploadRes = await fetch(`/api/submit/upload`, {
        method: 'POST',
        body: form,
        headers: { 'Accept': 'application/json' },
        credentials: 'include'
      });
      if (!uploadRes.ok) {
        // サーバが返すエラー詳細を表示
        let msg = 'アップロードに失敗しました';
        try {
          const ct = uploadRes.headers.get('Content-Type') || '';
          if (ct.includes('application/json')) {
            const j = await uploadRes.json();
            msg = j?.message || j?.error || msg;
          } else {
            msg = await uploadRes.text();
          }
        } catch {}
        throw new Error(msg || `HTTP ${uploadRes.status}`);
      }
      const data: any = await uploadRes.json();
      const imageUrl: string | undefined = data?.imageUrl;
      const videoUrl: string | undefined = data?.videoUrl;
      const displayFromServer: string | undefined = data?.displayImageUrl;
      const newItem: Submission = {
        id: `local-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        imageUrl: imageUrl || undefined,
        videoUrl: videoUrl || undefined,
        displayImageUrl: displayFromServer || imageUrl || videoUrl || undefined,
        createdAt: new Date().toISOString()
      };

      setSubmissions((prev) => {
        // ID重複を防ぐため、Setで管理
        const ids = new Set(prev.map((s) => s.id));
        if (ids.has(newItem.id)) return prev;
        const next = [newItem, ...prev];
        saveLocalSubmissions(anonId, next.filter((s) => s.id.startsWith('local-')));
        return next;
      });

      // タイムラインへ即時反映（ローカル）: アバターを使う
      const selfAvatar = resolveUploadUrl(profile?.avatarUrl) || null;
      setFeed((prev) => [
        {
          id: newItem.id,
          anonId,
          imageUrl: newItem.imageUrl || newItem.videoUrl || '',
          avatarUrl: selfAvatar || '',
          displayImageUrl: newItem.imageUrl || newItem.videoUrl || selfAvatar || '',
          createdAt: newItem.createdAt,
          title: titleBadge ?? null
        },
        ...prev,
      ]);

      // 2) 提出API（imageUrl を保存）
      const payload: any = {
        aim: (isVideo ? '動画提出' : '画像提出'),
        steps: ['準備', '実行', '完了'],
        frameType: 'none',
        ...(imageUrl ? { imageUrl } : {}),
        ...(videoUrl ? { videoUrl } : {})
      };

      let submitRes: SubmitResult | null = null;
      try {
        submitRes = await apiPost<SubmitResult, typeof payload>(`/api/submit`, payload);
      } catch {
        submitRes = { jpResult: 'none', probability: 0, bonusCount: 0, rewardTitle: undefined, rewardCardId: undefined, jackpotRecordedAt: null };
      }

      // アップロード中オーバーレイが閉じた後に演出開始
      setPendingFlow(submitRes);
      // スロットはOKボタンで閉じる（自動クローズはしない）

      // 称号などの更新反映 + 自分の提出物の再フェッチ（重複排除）
      try {
        // 即時にローカルの称号表示を更新
        if (submitRes?.rewardTitle) {
          setTitleBadge(submitRes.rewardTitle);
          setFeed((prev) => prev.map((it) => it.id === newItem.id ? { ...it, title: submitRes?.rewardTitle || it.title } : it));
        }
        // サーバの最新値で上書き（永続化の確認）
        const me = await apiGet<{ activeTitle?: string | null; activeTitleUntil?: string | null }>(`/api/user/me`);
        setTitleBadge(me.activeTitle ?? (submitRes?.rewardTitle ?? null));
        setTitleUntil(me.activeTitleUntil ?? null);
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(anonId)}`);
        setProfile(p);

        // 自分の提出物をサーバーの最新に完全同期し、ローカル一時提出をクリア（重複回避）
        const latest = await apiGet<{ items: Submission[] }>(`/api/submissions/me?limit=12`);
        setSubmissions(latest.items);
        saveLocalSubmissions(anonId, []);
      } catch {}
    } catch (e: any) {
      const msg = e?.message ?? 'アップロードに失敗しました';
      setUploadError(msg);
      toast.error(msg);
    } finally {
      const elapsed = Date.now() - startedAt;
      const remain = Math.max(0, 800 - elapsed);
      try { await new Promise((r) => setTimeout(r, remain)); } catch {}
      setUploading(false);
      toast.success('アップロードが完了しました');
    }
  }

  function onDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }

  function onDragLeave(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onUploadFile(f);
  }

  async function toggleLike(submissionId: string, currentLiked?: boolean) {
    setSubmissions((prev) => prev.map((it) => it.id === submissionId ? { ...it, liked: !currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? -1 : 1)) } : it));
    try {
      if (currentLiked) {
        await apiDelete<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`);
      } else {
        await apiPost<{ ok: boolean; likesCount: number; liked: boolean }>(`/api/submissions/${encodeURIComponent(submissionId)}/like`, {} as any);
      }
    } catch {
      // rollback
      setSubmissions((prev) => prev.map((it) => it.id === submissionId ? { ...it, liked: currentLiked, likesCount: Math.max(0, (it.likesCount ?? 0) + (currentLiked ? 1 : -1)) } : it));
    }
  }

  useEffect(() => {
    // 初回だけ強制リロード（ログイン直後のセッション同期のため）
    try {
      const key = 'toybox_mypage_force_reload';
      const shouldReload = typeof window !== 'undefined' && localStorage.getItem(key) === '1';
      if (shouldReload) {
        localStorage.removeItem(key);
        window.location.reload();
        return; // 以降の初期化はスキップ（リロード後に実行）
      }
    } catch {}

    (async () => {
      // ログイン状態を確認
      let userId: string | null = null;
      try {
        const me = await apiGet<{ ok: boolean; user: { anonId: string } | null }>(`/api/auth/me`);
        if (!me.ok || !me.user) {
          window.location.href = '/login';
          return;
        }
        userId = me.user.anonId;
        setAnonId(userId);
      } catch {
        window.location.href = '/login';
        return;
      }
      // API 取得（並列）
      const results = await Promise.allSettled([
        // topic は初期非表示のため取得しない
        apiGet<{ items: Submission[] }>(`/api/submissions/me?limit=12`),
        apiGet<{ activeTitle?: string | null; activeTitleUntil?: string | null }>(`/api/user/me`),
        apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(userId!)}`),
        apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=6`),
        apiGet<{ submitters: { anonId: string; displayName?: string | null }[] }>(`/api/submitters/today`),
        apiGet<{ ranking: { anonId: string; displayName?: string | null; count: number }[] }>(`/api/ranking/daily`),
      ]);
      const [subsR, userR, profR, feedR, subsTodayR, rankR] = results as any;
      setSubmissions(subsR.status === 'fulfilled' ? subsR.value.items : []);
      if (userR.status === 'fulfilled') {
        setTitleBadge(userR.value.activeTitle ?? null);
        setTitleUntil(userR.value.activeTitleUntil ?? null);
      } else {
        setTitleBadge(null);
        setTitleUntil(null);
      }
      setProfile(profR.status === 'fulfilled' ? profR.value : null);
      if (feedR.status === 'fulfilled') {
        setFeed(feedR.value.items);
        setNextCursor(feedR.value.nextCursor ?? null);
      } else {
        setFeed([]); setNextCursor(null);
      }
      setSubmitters(subsTodayR.status === 'fulfilled' ? subsTodayR.value.submitters : []);
      setRanking(rankR.status === 'fulfilled' ? rankR.value.ranking : []);

      // ローカル提出のマージ（サーバー未構築時の代替）+ 重複削除
      try {
        const locals = loadLocalSubmissions(userId!);
        if (locals.length > 0) {
          setSubmissions((prev) => {
            const ids = new Set(prev.map((p) => p.id));
            const merged = [...locals.filter((l) => !ids.has(l.id)), ...prev];
            // 重複IDを排除（念のため）
            const uniqueIds = new Set<string>();
            return merged.filter((m) => {
              if (uniqueIds.has(m.id)) return false;
              uniqueIds.add(m.id);
              return true;
            });
          });
        }
      } catch {}
    })();
  }, []);

  async function fetchTopic(kind: 'work' | 'play') {
    try {
      if (kind === 'work') { setTopicWorkVisible(true); setTopicWork('読み込み中…'); }
      else { setTopicPlayVisible(true); setTopicPlay('読み込み中…'); }
      const r = await apiGet<{ topic: string }>(`/api/topic/fetch?type=${encodeURIComponent(kind)}`);
      if (kind === 'work') setTopicWork(r.topic || '—'); else setTopicPlay(r.topic || '—');
    } catch {
      if (kind === 'work') setTopicWork('取得に失敗しました'); else setTopicPlay('取得に失敗しました');
    }
  }

  useEffect(() => {
    if (!uploading && pendingFlow) {
      (async () => {
        const res = pendingFlow; setPendingFlow(null);
        setFlowResult(res);
        if (res?.rewardCard) {
          const rc = res.rewardCard;
          const img = rc.image_url ? resolveUploadUrl(rc.image_url) : resolveUploadUrl(`/uploads/cards/${rc.card_id}.png`);
          setCardReveal({ imageUrl: img, cardName: rc.card_name, rarity: rc.rarity });
        } else {
          setCardReveal(null);
        }
        setFlowOpen(true);
        setFadeOut(false);
        setFlowPhase('card');
        // カード表示はタイマーで遷移しない。カードを閉じたら称号画面へ進む
      })();
    }
  }, [uploading, pendingFlow]);

 

  async function refreshWork() { try { const t = await apiGet<{ topic: string }>(`/api/topic/work`); setTopicWork(t.topic); } catch {} }
  async function refreshPlay() { try { const t = await apiGet<{ topic: string }>(`/api/topic/play`); setTopicPlay(t.topic); } catch {} }

  async function loadMore() {
    if (!nextCursor) return;
    if (feed.length >= FEED_MAX_ITEMS) return;
    try {
      const f = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=6&cursor=${encodeURIComponent(nextCursor)}`);
      setFeed((prev) => {
        const merged = [...prev, ...f.items];
        return merged.slice(0, FEED_MAX_ITEMS);
      });
      setNextCursor(f.nextCursor ?? null);
    } catch {}
  }

  return (
    <main className="mx-auto max-w-6xl p-4 grid grid-cols-12 gap-4">
      {/* アップロード中オーバーレイ */}
      {uploading && (
        <div className="fixed inset-0 z-[2000] bg-black/70 flex items-center justify-center">
          <div className="rounded-md border border-steam-iron-700 bg-steam-iron-900 text-steam-gold-200 px-6 py-4 shadow-xl">
            アップロード中…完了までお待ちください
          </div>
        </div>
      )}
      {/* 提出演出オーバーレイ */}
      {flowOpen && flowResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-lg md:max-w-xl rounded-md border border-steam-iron-700 bg-steam-iron-800 text-steam-gold-200 shadow-xl p-6 md:p-7">
            <div className={["transition-opacity duration-300", fadeOut ? 'opacity-0' : 'opacity-100'].join(' ')}>
              {flowPhase === 'card' && (
                cardReveal ? (
                  <CardReveal
                    imageUrl={cardReveal.imageUrl || undefined}
                    cardName={cardReveal.cardName}
                    rarity={cardReveal.rarity}
                    onClose={() => { setCardReveal(null); setFlowPhase('title'); }}
                  />
                ) : null
              )}
              {flowPhase === 'title' && (
                <div className="text-center space-y-4">
                  <div className="text-steam-gold-300 font-semibold text-lg md:text-xl">称号を取得しました！</div>
                  <div className="mt-2 flex justify-center">
                    <img src="/sample_2.svg" alt="dummy title" className="h-24 md:h-32 w-auto" />
                  </div>
                  <div className="mt-1 text-xl md:text-2xl font-bold text-steam-gold-300">{flowResult.rewardTitle || '—'}</div>
                  <div className="mt-4">
                    <button
                      onClick={async () => {
                        if (okLoading) return;
                        setOkLoading(true);
                        try {
                          const r = await apiPost<{ ok: boolean; title?: string; until?: string | null }, {}>('/api/user/nextTitle', {} as any);
                          if (r?.title) {
                            setTitleBadge(r.title || null);
                            setFlowResult((prev) => prev ? { ...prev, rewardTitle: r.title || prev.rewardTitle } : prev);
                          }
                        } catch {}
                        setFlowOpen(false);
                        setFlowPhase('done');
                        try { window.location.reload(); } catch {}
                      }}
                      className="rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600"
                    >OK</button>
                  </div>
                </div>
              )}
              {/* スロット演出はジャックポット廃止のため削除 */}
            </div>
          </div>
        </div>
      )}
      {/* 左カラム */}
      <aside className="col-span-12 md:col-span-3 space-y-4">
        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">プロフィール</h2>
          <div className="mt-2 flex flex-col items-center gap-3">
            <div className="h-[200px] w-[200px] overflow-hidden rounded-full border border-steam-iron-700 bg-steam-iron-800 flex items-center justify-center text-sm text-steam-iron-400">
              {resolveUploadUrl(profile?.avatarUrl) ? (
                <img src={resolveUploadUrl(profile?.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
              ) : (
                <span>未設定</span>
              )}
            </div>
            <div className="text-steam-iron-100 font-semibold text-sm">{profile?.displayName || profile?.anonId || '—'}</div>
            <div className="text-xs leading-relaxed text-steam-iron-200 text-center px-1">
              {(() => {
                const bio = profile?.bio || '';
                const isLong = bio.length > 100;
                const short = isLong ? bio.slice(0, 100) + '…' : bio || '—';
                return short;
              })()}
              {profile?.bio && profile.bio.length > 100 && (
                <div className="mt-1">
                  <Link href="/profile/view" className="text-steam-gold-400 underline text-[11px]">続きを見る</Link>
                </div>
              )}
            </div>
            <div className="text-sm text-steam-gold-300">称号: {titleBadge ?? '—'}</div>
            {titleUntil && (
              <div className="text-xs text-steam-iron-300">有効期限: {new Date(titleUntil).toLocaleDateString()}</div>
            )}
          </div>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">リンク</h2>
          <ul className="space-y-2 text-steam-iron-100 text-sm list-disc pl-5">
            <li><a href="https://discord.com/" target="_blank" rel="noreferrer" className="text-steam-gold-400 underline">Discord</a></li>
            <li><a href="https://chat.openai.com/" target="_blank" rel="noreferrer" className="text-steam-gold-400 underline">AI サイト</a></li>
            <li><a href="/" className="text-steam-gold-400 underline">当社LP</a></li>
            <li><a href="/terms" className="text-steam-gold-400 underline">利用規約</a></li>
            <li><a href="/contact" className="text-steam-gold-400 underline">お問い合わせ</a></li>
          </ul>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">お仕事系のお題</h2>
          {topicWorkVisible ? (
            <div className="text-steam-iron-100 text-sm">{topicWork}</div>
          ) : null}
          <a href="https://ayatori-inc.co.jp/toybox-std/" target="_blank" rel="noreferrer" onClick={() => { fetchTopic('work'); }} className="inline-block mt-3 rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600 text-base">お題を見る</a>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">ゲームのお題</h2>
          {topicPlayVisible ? (
            <div className="text-steam-iron-100 text-sm">{topicPlay}</div>
          ) : null}
          <a href="https://ayatori-inc.co.jp/toybox-game/" target="_blank" rel="noreferrer" onClick={() => { fetchTopic('play'); }} className="inline-block mt-3 rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600 text-base">お題を見る</a>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">アカウント</h2>
          <button
            onClick={async () => {
              if (!confirm('アカウントを削除します。提出物・プロフィールを含む全データが消えます。よろしいですか？')) return;
              try {
                const res = await fetch(`/api/auth/deleteAccount`, { method: 'POST', credentials: 'include' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                alert('アカウントを削除しました');
                try { window.location.href = '/'; } catch {}
              } catch (e: any) {
                alert(e?.message || 'アカウント削除に失敗しました');
              }
            }}
            className="w-full rounded bg-red-700 px-4 py-2 text-white hover:bg-red-600"
          >アカウント削除</button>
        </section>
      </aside>

      {/* 中央カラム */}
      <section className="col-span-12 md:col-span-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-steam-gold-300 font-semibold">自分の提出物</h2>
          {anonId && <Link href={'/profile'} className="text-xs text-steam-gold-400 underline">プロフィール設定</Link>}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {submissions.length === 0 && Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded border border-steam-iron-800 bg-steam-iron-900" />
          ))}
          {submissions.map((s) => (
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
                  onClick={() => { const u = resolveUploadUrl(s.videoUrl); if (u) { setLightboxSrc(u); setLightboxType('video'); setLightboxAsset({ id: s.id, type: 'video', title: s.id, authorName: profile?.displayName || anonId || undefined, mimeType: 'video/mp4', fileUrl: u }); setLightboxOpen(true); } }}
                >
                  <video
                    src={resolveUploadUrl(s.displayImageUrl || s.videoUrl)}
                    className="max-h-full max-w-full object-contain rounded"
                    muted
                    preload="metadata"
                  />
                  {/* play overlay */}
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
                  src={resolveUploadUrl(s.displayImageUrl || s.imageUrl)}
                  alt="submission"
                  className="w-full aspect-square object-contain p-3 cursor-zoom-in"
                  onClick={() => { const u = resolveUploadUrl(s.displayImageUrl || s.imageUrl); if (u) { setLightboxSrc(u); setLightboxType('image'); setLightboxAsset({ id: s.id, type: 'image', title: s.id, authorName: profile?.displayName || anonId || undefined, mimeType: 'image/png', fileUrl: u }); setLightboxOpen(true); } }}
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
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c0 .69.28 1.32.73 1.77.45.45 1.08.73 1.77.73H21a2 2 0 1 1 0 4h-.09c-.69 0-1.32.28-1.77.73-.45.45-.73 1.08-.73 1.77z"/>
                  </svg>
                  開く
                </a>
              )}
              <button
                onClick={async () => {
                  if (!confirm('この提出を削除します。よろしいですか？')) return;
                  try {
                    // ローカル一時IDはサーバー側に存在しないため、ローカルだけで削除
                    if (s.id.startsWith('local-')) {
                      setSubmissions(prev => {
                        const next = prev.filter(x => x.id !== s.id);
                        if (anonId) {
                          // ローカル保存も更新
                          saveLocalSubmissions(anonId, next.filter(it => it.id.startsWith('local-')));
                        }
                        return next;
                      });
                      setFeed(prev => prev.filter(x => x.id !== s.id));
                      return;
                    }

                    await apiDelete<{ ok: boolean }>(`/api/submissions/${encodeURIComponent(s.id)}`);
                    setSubmissions(prev => prev.filter(x => x.id !== s.id));
                    setFeed(prev => prev.filter(x => x.id !== s.id));
                    // 念のためサーバー側の最新に同期
                    try {
                      const latest = await apiGet<{ items: Submission[] }>(`/api/submissions/me?limit=12`);
                      setSubmissions(latest.items);
                    } catch {}
                  } catch (e: any) {
                    alert(e?.message || '削除に失敗しました');
                  }
                }}
                className="hidden group-hover:block absolute top-2 right-2 rounded bg-red-600/90 text-white text-xs px-2 py-1 hover:bg-red-500"
                aria-label="削除"
              >削除</button>
            </div>
          ))}
        </div>
      </section>

      {/* Lightbox */}
      <ImageLightbox src={lightboxSrc} alt="submission" open={lightboxOpen} onClose={() => setLightboxOpen(false)} type={lightboxType} asset={lightboxAsset || undefined} />

      {/* 右カラム */}
      <aside className="col-span-12 md:col-span-3 space-y-4">
        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">本日の課題提出</h2>
          <div className="space-y-2">
            <input id="upload-input" type="file" accept="image/png,image/jpeg,video/mp4,video/webm,video/ogg" className="hidden" onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUploadFile(f);
              e.currentTarget.value = '';
            }} />
            <div
              role="button"
              tabIndex={0}
              onClick={() => document.getElementById('upload-input')?.click()}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById('upload-input')?.click(); }}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              className={[
                'flex flex-col items-center justify-center rounded border-2 border-dashed p-6 text-center select-none',
                isDragging ? 'border-steam-gold-500 bg-steam-iron-800/50' : 'border-steam-iron-700 bg-steam-iron-900'
              ].join(' ')}
            >
              <svg aria-hidden="true" width="40" height="40" viewBox="0 0 24 24" className="text-steam-gold-400 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 16V4" />
                <path d="M8 8l4-4 4 4" />
                <rect x="3" y="16" width="18" height="4" rx="1" ry="1" />
              </svg>
              <div className="text-sm text-steAM-gold-200">課題をアップロード（PNG/JPEG/MP4）</div>
              <div className="text-xs text-steam-iron-300">ここにドラッグ＆ドロップ、またはクリックして選択</div>
              {uploading && <div className="mt-2 text-xs text-steam-iron-200">アップロード中…</div>}
            </div>
            {uploadError && <div className="text-xs text-red-400">{uploadError}</div>}
            <p className="text-xs text-steam-iron-300">選んだ画像は「自分の提出物」に即時反映・ローカル保存されます。</p>
          </div>
        </section>

        {/* ゲームZIPアップロード */}
        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">ゲームをアップロード（ZIP）</h2>
          <div className="space-y-2">
            <input id="upload-game-input" type="file" accept=".zip,application/zip" className="hidden" onChange={async (e) => {
              const f = e.target.files?.[0];
              if (!f) { try { (e.target as HTMLInputElement).value=''; } catch {} return; }
              setUploadError(null);
              setUploading(true);
              const startedAt = Date.now();
              try {
                const form = new FormData();
                form.append('file', f);
                const res = await fetch(`/api/submit/uploadGame`, { method: 'POST', body: form, headers: { 'Accept': 'application/json' }, credentials: 'include' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const { gameUrl }: { gameUrl: string } = await res.json();
                const payload: any = { aim: 'ゲーム提出', steps: ['準備','実行','完了'], frameType: 'none', gameUrl };
                let submitRes: SubmitResult | null = null;
                try { submitRes = await apiPost<SubmitResult, typeof payload>(`/api/submit`, payload); } catch { submitRes = { jpResult: 'none', probability: 0, bonusCount: 0, rewardTitle: undefined, rewardCardId: undefined, jackpotRecordedAt: null }; }
                const now = new Date().toISOString();
                const tmp: Submission = { id: `local-${Date.now()}-${Math.random().toString(36).slice(2)}`, imageUrl: '/uploads/sample_3.svg', displayImageUrl: '/uploads/sample_3.svg', createdAt: now, gameUrl };
                setSubmissions((prev) => [tmp, ...prev]);
                // 画像/動画アップロードと同じフロー制御（アップロード完了後に演出開始）
                setPendingFlow(submitRes);
              } catch (err: any) {
                toast.error(err?.message || 'ゲームのアップロードに失敗しました');
              } finally {
                const elapsed = Date.now() - startedAt;
                const remain = Math.max(0, 800 - elapsed);
                try { await new Promise((r) => setTimeout(r, remain)); } catch {}
                setUploading(false);
                try { (e.target as HTMLInputElement).value=''; } catch {}
              }
            }} />
            <button onClick={() => document.getElementById('upload-game-input')?.click()} className="w-full rounded bg-fuchsia-600 px-4 py-2 text-white hover:bg-fuchsia-500">ZIPを選択</button>
            <p className="text-xs text-steam-iron-300">必ずindex.htmlを含む <strong className="text-steam-gold-300">Webブラウザでできるミニゲームで構成されたZIPファイル</strong> をアップロードするようにしてください。</p>
          </div>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">タイムライン</h2>
          <ul className="space-y-2 text-sm text-steam-iron-100">
            {feed.length === 0 && <li>データなし</li>}
            {feed.map((f) => (
              <li key={f.id} className="flex items-center gap-2">
                <div className="h-10 w-10 overflow-hidden rounded-full border-4 border-steam-iron-900 ring-2 ring-steam-iron-700 bg-steam-iron-800 flex items-center justify-center text-steam-iron-300 flex-none">
                  {resolveUploadUrl(f.avatarUrl || undefined) ? (
                    <img src={resolveUploadUrl(f.avatarUrl || undefined)} alt="avatar" className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-xs">{f.anonId.slice(0,2).toUpperCase()}</span>
                  )}
                </div>
                <div className="min-w-0">
                  {anonId && f.anonId === anonId ? (
                    <Link href={`/profile/view`} className="text-steam-gold-200 hover:underline block truncate max-w-[140px] md:max-w-[220px]">{f.displayName || f.anonId}</Link>
                  ) : (
                    <Link href={`/${encodeURIComponent(f.anonId)}`} className="text-steam-gold-200 hover:underline block truncate max-w-[140px] md:max-w-[220px]">{f.displayName || f.anonId}</Link>
                  )}
                  <div className="text-[11px] text-steam-iron-300">{f.title ? f.title : '—'}</div>
                </div>
              </li>
            ))}
          </ul>
          {nextCursor && feed.length < FEED_MAX_ITEMS && (
            <button onClick={loadMore} className="mt-3 w-full rounded bg-steam-iron-800 px-3 py-1 text-steam-gold-300 hover:bg-steam-iron-700">
              さらに読み込む
            </button>
          )}
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">提出者（当日）</h2>
          <div className="text-sm text-steam-iron-100 mb-2">{submitters.length}名</div>
          <ul className="space-y-1 text-xs text-steam-iron-200 max-h-40 overflow-auto">
            {submitters.map((s) => (
              <li key={s.anonId}>
                {anonId && s.anonId === anonId ? (
                  <Link href={`/profile/view`} className="hover:underline text-steam-gold-200">{s.displayName || s.anonId}</Link>
                ) : (
                  <Link href={`/${encodeURIComponent(s.anonId)}`} className="hover:underline text-steam-gold-200">{s.displayName || s.anonId}</Link>
                )}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">デイリーランキング</h2>
          <ol className="space-y-1 text-sm text-steam-iron-100 list-decimal pl-5">
            {ranking.length === 0 && <li>データなし</li>}
            {ranking.map((r) => (
              <li key={r.anonId}>
                {anonId && r.anonId === anonId ? (
                  <Link href={`/profile/view`} className="text-steam-gold-200 hover:underline">{r.displayName || r.anonId}</Link>
                ) : (
                  <Link href={`/${encodeURIComponent(r.anonId)}`} className="text-steam-gold-200 hover:underline">{r.displayName || r.anonId}</Link>
                )} {r.count}件
              </li>
            ))}
          </ol>
        </section>
      </aside>
    </main>
  );
}


