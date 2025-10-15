'use client';
import React, { useEffect, useState } from 'react';
import { useParams, redirect } from 'next/navigation';
import { API_BASE, apiGet, apiPost, apiUpload } from '../../../lib/api';
import { getAnonId } from '../../../lib/auth';

type Submission = { id: string; imageUrl: string; createdAt: string };
type PublicProfile = {
  anonId: string;
  activeTitle?: string | null;
  activeTitleUntil?: string | null;
  displayName?: string | null;
  avatarUrl?: string | null;
  headerUrl?: string | null;
  bio?: string;
};

export default function UserProfilePage() {
  const params = useParams<{ anonId: string }>();
  const anonId = params?.anonId;
  // このルートは旧パス互換。新URL `/${anonId}` へリダイレクト
  if (anonId) {
    try { redirect(`/${encodeURIComponent(anonId)}`); } catch {}
  }
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [items, setItems] = useState<Submission[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [editingBio, setEditingBio] = useState<string>('');
  const [isOwner, setIsOwner] = useState<boolean>(false);
  const [editingName, setEditingName] = useState<string>('');

  useEffect(() => {
    if (!anonId) return;
    (async () => {
      try {
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(anonId)}`);
        setProfile(p);
        setEditingBio(p.bio || '');
        setEditingName(p.displayName || '');
        setIsOwner(getAnonId() === anonId);
      } catch { setProfile(null); }
      try {
        const s = await apiGet<{ items: Submission[]; nextCursor: string | null }>(`/api/user/submissions/${encodeURIComponent(anonId)}?limit=12`);
        // まずサーバのアイテムを適用
        let merged: Submission[] = s.items;
        // 自分のプロフィール閲覧時はローカル保存の提出もマージ
        try {
          if (getAnonId() === anonId) {
            const locals: Submission[] = loadLocalSubmissions(anonId);
            if (locals.length > 0) {
              const seen = new Set(merged.map((x) => x.id));
              const onlyLocals = locals.filter((l) => !seen.has(l.id));
              // 新しい順でローカルを先頭に
              merged = [...onlyLocals, ...merged];
            }
          }
        } catch {}
        setItems(merged);
        setNextCursor(s.nextCursor ?? null);
      } catch { setItems([]); setNextCursor(null); }
    })();
  }, [anonId]);

  async function loadMore() {
    if (!nextCursor || !anonId) return;
    try {
      const s = await apiGet<{ items: Submission[]; nextCursor: string | null }>(`/api/user/submissions/${encodeURIComponent(anonId)}?limit=12&cursor=${encodeURIComponent(nextCursor)}`);
      setItems((prev) => [...prev, ...s.items]);
      setNextCursor(s.nextCursor ?? null);
    } catch {}
  }

  function resolveUploadUrl(u?: string | null): string | undefined {
    if (!u) return undefined;
    if (u.startsWith('/uploads/')) return `${API_BASE}${u}`;
    return u;
  }

  async function saveBio() {
    if (!isOwner) return;
    try {
      const res = await apiPost<{ ok: boolean; bio: string }>(`/api/user/profile/bio`, { bio: editingBio }, { anonId: getAnonId() || undefined });
      setProfile((p) => (p ? { ...p, bio: res.bio } : p));
    } catch {}
  }

  async function saveName() {
    if (!isOwner) return;
    try {
      const res = await apiPost<{ ok: boolean; displayName: string }>(`/api/user/profile/name`, { displayName: editingName }, { anonId: getAnonId() || undefined });
      setProfile((p) => (p ? { ...p, displayName: res.displayName } : p));
    } catch {}
  }

  async function uploadImage(kind: 'avatar' | 'header', file: File) {
    if (!isOwner) return;
    try {
      const q = new URLSearchParams({ kind }).toString();
      const res = await apiUpload<{ ok: boolean; avatarUrl?: string; headerUrl?: string }>(`/api/user/profile/upload?${q}`, file, { anonId: getAnonId() || undefined });
      setProfile((p) => (p ? { ...p, ...(res.avatarUrl ? { avatarUrl: res.avatarUrl } : {}), ...(res.headerUrl ? { headerUrl: res.headerUrl } : {}) } : p));
    } catch {}
  }

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

  return (
    <main className="mx-auto max-w-6xl p-4">
      <h1 className="mb-3 text-2xl font-bold text-steam-gold-300">プロフィール</h1>
      {profile ? (
        <section className="mb-6 overflow-hidden rounded border border-steam-iron-700 bg-steam-iron-900">
          {/* Header image */}
          <div className="relative h-40 w-full bg-steam-iron-800">
            {resolveUploadUrl(profile.headerUrl) ? (
              <img src={resolveUploadUrl(profile.headerUrl)} alt="header" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">NO Image</div>
            )}
            {isOwner ? (
              <label className="absolute right-3 bottom-3 cursor-pointer rounded bg-steam-iron-800/80 px-2 py-1 text-xs text-steam-gold-300 hover:bg-steam-iron-700">
                ヘッダー変更
                <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadImage('header', f); }} />
              </label>
            ) : null}
          </div>
          {/* Avatar + basic info */}
          <div className="flex items-start gap-4 p-3">
            <div className="relative -mt-10 h-20 w-20 flex-shrink-0 overflow-hidden rounded-full border-2 border-steam-iron-700 bg-steam-iron-800">
              {resolveUploadUrl(profile.avatarUrl) ? (
                <img src={resolveUploadUrl(profile.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-xs">未設定</div>
              )}
              {isOwner ? (
                <label className="absolute bottom-0 right-0 m-1 cursor-pointer rounded bg-steam-iron-800/80 px-1 text-[10px] text-steam-gold-300 hover:bg-steam-iron-700">
                  変更
                  <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadImage('avatar', f); }} />
                </label>
              ) : null}
            </div>
            <div className="flex-1">
              <div className="text-steam-iron-100 text-lg font-semibold">{profile.anonId}</div>
              <div className="mt-1 text-sm text-steam-iron-100">{profile.displayName || '—'}</div>
              <div className="text-sm text-steam-gold-300">称号: {profile.activeTitle || '—'}</div>
              {profile.activeTitleUntil && (
                <div className="text-xs text-steam-iron-300">有効期限: {new Date(profile.activeTitleUntil).toLocaleDateString()}</div>
              )}
            </div>
          </div>
          {/* Bio */}
          {profile.bio ? (
            <div className="px-3 pb-3 text-sm leading-relaxed text-steam-iron-200 whitespace-pre-wrap">
              {profile.bio}
            </div>
          ) : null}
        </section>
      ) : (
        <div className="mb-6 h-20 animate-pulse rounded border border-steam-iron-800 bg-steam-iron-900" />
      )}

      <h2 className="mb-3 text-steam-gold-300 font-semibold">提出一覧</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {items.map((s) => (
          <div key={s.id} className="rounded border border-steam-iron-700 bg-steam-iron-900">
            <img loading="lazy" src={s.imageUrl} alt="submission" className="w-full aspect-square object-contain p-2" />
          </div>
        ))}
      </div>
      {nextCursor && (
        <button onClick={loadMore} className="mt-4 rounded bg-steam-iron-800 px-3 py-1 text-steam-gold-300 hover:bg-steam-iron-700">さらに読み込む</button>
      )}
    </main>
  );
}


