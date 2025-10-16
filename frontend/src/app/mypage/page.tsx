'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
// 匿名IDは廃止。必要時は /api/auth/me から取得
import { API_BASE, apiGet, apiPost, apiDelete } from '../../lib/api';
import CardReveal from '../../components/CardReveal';
import SlotMachine from '../../components/SlotMachine';

type Submission = { id: string; imageUrl: string; displayImageUrl?: string; createdAt: string };
type FeedItem = { id: string; anonId: string; displayName?: string | null; imageUrl: string; avatarUrl?: string | null; displayImageUrl?: string; createdAt: string; title?: string | null };
  type PublicProfile = { anonId: string; displayName?: string | null; avatarUrl?: string | null; bio?: string | null; updatedAt?: string | null };

type SubmitResult = {
  jpResult: 'win' | 'lose' | 'none';
  probability: number;
  bonusCount: number;
  rewardTitle?: string;
  rewardCardId?: string;
  rewardCard?: { card_id: string; card_name: string; rarity?: 'SSR' | 'SR' | 'R' | 'N'; image_url?: string | null };
  jackpotRecordedAt?: string | null;
};

export default function MyPage() {
  const [anonId, setAnonId] = useState<string | null>(null);
  const [topicWork, setTopicWork] = useState<string>('読み込み中…');
  const [topicPlay, setTopicPlay] = useState<string>('読み込み中…');
  const [titleBadge, setTitleBadge] = useState<string | null>(null);
  const [titleUntil, setTitleUntil] = useState<string | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [submitters, setSubmitters] = useState<{ anonId: string; displayName?: string | null }[]>([]);
  const [ranking, setRanking] = useState<{ anonId: string; displayName?: string | null; count: number }[]>([]);
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // 提出後の演出オーバーレイ
  const [flowOpen, setFlowOpen] = useState(false);
  const [flowPhase, setFlowPhase] = useState<'idle'|'card'|'title'|'slot'|'done'>('idle');
  const [flowResult, setFlowResult] = useState<SubmitResult | null>(null);
  const [fadeOut, setFadeOut] = useState(false);
  const [slotFinished, setSlotFinished] = useState(false);
  const [cardReveal, setCardReveal] = useState<{ imageUrl?: string | null; cardName: string; rarity?: 'SSR' | 'SR' | 'R' | 'N' } | null>(null);

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
    setUploading(true);
    try {
      // PNG/JPEG のみ許可
      const isJpeg = file.type === 'image/jpeg' || /\.(jpe?g)$/i.test(file.name);
      const isPng = file.type === 'image/png' || /\.(png)$/i.test(file.name);
      if (!isJpeg && !isPng) {
        throw new Error('PNG または JPEG のみ対応しています');
      }
      // 10MB 制限（任意）
      if (file.size > 10 * 1024 * 1024) {
        throw new Error('ファイルサイズが大きすぎます（最大10MB）');
      }
      // 1) 画像を先にサーバへアップロードし、相対URLを取得
      const form = new FormData();
      form.append('file', file);
      const uploadRes = await fetch(`${API_BASE}/api/submit/upload`, {
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
      const { imageUrl }: { imageUrl: string } = await uploadRes.json();
      const newItem: Submission = {
        id: `local-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        imageUrl: imageUrl.startsWith('/uploads/') ? `${API_BASE}${imageUrl}` : imageUrl,
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
      const selfAvatar = resolveUploadUrl(profile?.avatarUrl, profile?.updatedAt) || null;
      setFeed((prev) => [
        {
          id: newItem.id,
          anonId,
          imageUrl: newItem.imageUrl,
          avatarUrl: selfAvatar || '',
          displayImageUrl: newItem.imageUrl || selfAvatar || '',
          createdAt: newItem.createdAt,
          title: titleBadge ?? null
        },
        ...prev,
      ]);

      // 2) 提出API（imageUrl を保存）
      const payload = {
        aim: '画像提出',
        steps: ['準備', '実行', '完了'],
        frameType: 'default',
        imageUrl
      };

      let submitRes: SubmitResult | null = null;
      try {
        submitRes = await apiPost<SubmitResult, typeof payload>(`/api/submit`, payload);
      } catch {
        submitRes = { jpResult: 'none', probability: 0, bonusCount: 0, rewardTitle: undefined, rewardCardId: undefined, jackpotRecordedAt: null };
      }

      // 演出開始（カード→称号→スロット）
      setFlowResult(submitRes);
      // カード表示データを反映（APIが返す rewardCard を使用）
      if (submitRes?.rewardCard) {
        setCardReveal({
          imageUrl: resolveUploadUrl(submitRes.rewardCard.image_url),
          cardName: submitRes.rewardCard.card_name,
          rarity: submitRes.rewardCard.rarity
        });
      } else {
        setCardReveal(null);
      }
      setFlowOpen(true);
      setFadeOut(false);
      setFlowPhase('card');
      // カード取得はバックエンドの即時報酬に一本化（フロント側の追加生成は行わない）
      await new Promise((r) => setTimeout(r, 3000));
      // フェードアウトして次のフェーズへ
      setFadeOut(true);
      await new Promise((r) => setTimeout(r, 300));
      setFlowPhase('title');
      setFadeOut(false);
      await new Promise((r) => setTimeout(r, 3000));
      setFadeOut(true);
      await new Promise((r) => setTimeout(r, 300));
      setFlowPhase('slot');
      setSlotFinished(false);
      setFadeOut(false);
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
      setUploadError(e?.message ?? 'アップロードに失敗しました');
    } finally {
      setUploading(false);
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
      // API 取得
      try { const tw = await apiGet<{ topic: string }>(`/api/topic/work`); setTopicWork(tw.topic); } catch { setTopicWork('—'); }
      try { const tp = await apiGet<{ topic: string }>(`/api/topic/play`); setTopicPlay(tp.topic); } catch { setTopicPlay('—'); }
      try {
        const subs = await apiGet<{ items: Submission[] }>(`/api/submissions/me?limit=12`);
        setSubmissions(subs.items);
      } catch {
        setSubmissions([]);
      }
      // 称号は当面 user/me から（null 許容）
      try {
        const user = await apiGet<{ activeTitle?: string | null; activeTitleUntil?: string | null }>(`/api/user/me`);
        setTitleBadge(user.activeTitle ?? null);
        setTitleUntil(user.activeTitleUntil ?? null);
      } catch {
        setTitleBadge(null);
        setTitleUntil(null);
      }

      // 公開プロフィール（アイコン・プロフィール文）
      try {
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(userId!)}`);
        setProfile(p);
      } catch {
        setProfile(null);
      }

      try {
        const f = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=6`);
        setFeed(f.items);
        setNextCursor(f.nextCursor ?? null);
      } catch { setFeed([]); setNextCursor(null); }

      try {
        const s = await apiGet<{ submitters: { anonId: string; displayName?: string | null }[] }>(`/api/submitters/today`);
        setSubmitters(s.submitters);
      } catch { setSubmitters([]); }

      try {
        const r = await apiGet<{ ranking: { anonId: string; displayName?: string | null; count: number }[] }>(`/api/ranking/daily`);
        setRanking(r.ranking);
      } catch { setRanking([]); }

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

function resolveUploadUrl(u?: string | null, updatedAt?: string | null): string | undefined {
  if (!u) return undefined;
  const base = u.startsWith('/uploads/') ? `${API_BASE}${u}` : u;
  if (!updatedAt) return base;
  const q = `t=${new Date(updatedAt).getTime()}`;
  return base.includes('?') ? base : `${base}?${q}`;
}

  async function refreshWork() { try { const t = await apiGet<{ topic: string }>(`/api/topic/work`); setTopicWork(t.topic); } catch {} }
  async function refreshPlay() { try { const t = await apiGet<{ topic: string }>(`/api/topic/play`); setTopicPlay(t.topic); } catch {} }

  async function loadMore() {
    if (!nextCursor) return;
    try {
      const f = await apiGet<{ items: FeedItem[]; nextCursor: string | null }>(`/api/feed?limit=6&cursor=${encodeURIComponent(nextCursor)}`);
      setFeed((prev) => [...prev, ...f.items]);
      setNextCursor(f.nextCursor ?? null);
    } catch {}
  }

  return (
    <main className="mx-auto max-w-6xl p-4 grid grid-cols-12 gap-4">
      {/* 提出演出オーバーレイ */}
      {flowOpen && flowResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-lg md:max-w-xl rounded-md border border-steam-iron-700 bg-steam-iron-800 text-steam-gold-200 shadow-xl p-6 md:p-7">
            <div className={["transition-opacity duration-300", fadeOut ? 'opacity-0' : 'opacity-100'].join(' ')}>
              {flowPhase === 'card' && (
                cardReveal ? (
                  <CardReveal imageUrl={cardReveal.imageUrl || undefined} cardName={cardReveal.cardName} rarity={cardReveal.rarity} onClose={() => setCardReveal(null)} />
                ) : (
                  <div className="text-center space-y-4">
                    <div className="text-steam-gold-300 font-semibold text-lg md:text-xl">カードを取得しました！</div>
                    <div className="mt-2 flex justify-center">
                      <img src="/uploads/sample_1.svg" alt="dummy card" className="h-28 md:h-36 w-auto" />
                    </div>
                  </div>
                )
              )}
              {flowPhase === 'title' && (
                <div className="text-center space-y-4">
                  <div className="text-steam-gold-300 font-semibold text-lg md:text-xl">称号を取得しました！</div>
                  <div className="mt-2 flex justify-center">
                    <img src="/uploads/sample_2.svg" alt="dummy title" className="h-24 md:h-32 w-auto" />
                  </div>
                  <div className="mt-1 text-xl md:text-2xl font-bold text-steam-gold-300">{flowResult.rewardTitle || '—'}</div>
                </div>
              )}
              {flowPhase === 'slot' && (
                <div>
                  <div className="mb-2 text-center text-steam-iron-100">ジャックポット抽選（本日初投稿のみ対象）</div>
                  <SlotMachine result={flowResult.jpResult} onFinished={() => setSlotFinished(true)} durationMs={3000} />
                  {slotFinished && (
                    <div className="mt-3 text-center">
                      {flowResult.jpResult === 'win' ? (
                        <div className="space-y-2">
                          <div className="text-lg font-semibold text-steam-gold-300">当たり！</div>
                          <div className="text-sm text-steam-iron-200">おめでとうございます！</div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div className="text-lg font-semibold text-steam-brown-300">残念…</div>
                          <div className="text-sm text-steam-iron-200">また明日チャレンジ！</div>
                        </div>
                      )}
                      <button
                        onClick={() => { setFlowOpen(false); setFlowPhase('done'); try { window.location.reload(); } catch {} }}
                        className="mt-4 rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600"
                      >OK</button>
                    </div>
                  )}
                </div>
              )}
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
          </ul>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">お仕事系のお題</h2>
          <div className="text-steam-iron-100 text-sm">{topicWork}</div>
          <a href="https://ayatori-inc.co.jp/toybox-std/" target="_blank" rel="noreferrer" className="inline-block mt-3 rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600 text-base">お題を見る</a>
        </section>

        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">ゲームのお題</h2>
          <div className="text-steam-iron-100 text-sm">{topicPlay}</div>
          <a href="https://ayatori-inc.co.jp/toybox-game/" target="_blank" rel="noreferrer" className="inline-block mt-3 rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600 text-base">お題を見る</a>
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
            <div key={s.id} className="relative rounded border border-steam-iron-700 bg-steam-iron-900 group">
              <img loading="lazy" src={resolveUploadUrl(s.displayImageUrl || s.imageUrl)} alt="submission" className="w-full aspect-square object-contain p-3" />
              <div className="absolute inset-0 pointer-events-none ring-2 ring-steam-gold-500/60 rounded animate-pulse"></div>
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

      {/* 右カラム */}
      <aside className="col-span-12 md:col-span-3 space-y-4">
        <section className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
          <h2 className="mb-2 text-steam-gold-300 font-semibold">本日の課題提出</h2>
          <div className="space-y-2">
            <input id="upload-input" type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => {
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
              <div className="text-sm text-steam-gold-200">課題をアップロード（PNG/JPEG）</div>
              <div className="text-xs text-steam-iron-300">ここにドラッグ＆ドロップ、またはクリックして選択</div>
              {uploading && <div className="mt-2 text-xs text-steam-iron-200">アップロード中…</div>}
            </div>
            {uploadError && <div className="text-xs text-red-400">{uploadError}</div>}
            <p className="text-xs text-steam-iron-300">選んだ画像は「自分の提出物」に即時反映・ローカル保存されます。</p>
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
          {nextCursor && (
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


