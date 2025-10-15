"use client";
import React, { useEffect, useState } from 'react';
import { API_BASE, apiGet, apiPost, apiPatch, apiUpload } from '../../lib/api';
// 匿名IDは廃止。/api/auth/me から取得

type PublicProfile = {
  anonId: string;
  displayName?: string | null;
  avatarUrl?: string | null;
  headerUrl?: string | null;
  bio?: string | null;
  activeTitle?: string | null;
  activeTitleUntil?: string | null;
};

type UserMe = {
  anonId: string;
  activeTitle: string | null;
  activeTitleUntil: string | null;
  cardsAlbum: any[];
  lotteryBonusCount: number;
};

export default function ProfileSettingsPage() {
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      let a: string | null = null;
      try {
        const me = await apiGet<{ ok: boolean; user: { anonId: string } | null }>(`/api/auth/me`);
        a = me.ok && me.user ? me.user.anonId : null;
      } catch {}
      if (!a) { window.location.href = '/login'; return; }
      try {
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(a)}`);
        setProfile(p);
        setName(p.displayName || '');
        setBio(p.bio || '');
      } catch { /* noop */ }
    })();
  }, []);

  function resolveUploadUrl(u?: string | null): string | undefined {
    if (!u) return undefined;
    if (u.startsWith('/uploads/')) return `${API_BASE}${u}`;
    return u;
  }

  async function saveName() {
    try {
      await apiPatch<UserMe>(`/api/user/profile`, { displayName: name });
      // /api/user/me を再フェッチしてグローバル状態を更新
      await refreshProfile();
      setMsg('名前を保存しました');
      setTimeout(() => setMsg(null), 2000);
    } catch {}
  }

  async function saveBio() {
    try {
      await apiPatch<UserMe>(`/api/user/profile`, { bio });
      // /api/user/me を再フェッチしてグローバル状態を更新
      await refreshProfile();
      setMsg('プロフィール文を保存しました');
      setTimeout(() => setMsg(null), 2000);
    } catch {}
  }

  async function refreshProfile() {
    let a: string | null = null;
    try {
      const me = await apiGet<{ ok: boolean; user: { anonId: string } | null }>(`/api/auth/me`);
      a = me.ok && me.user ? me.user.anonId : null;
    } catch {}
    if (!a) return;
    try {
      const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(a)}`);
      setProfile(p);
      setName(p.displayName || '');
      setBio(p.bio || '');
    } catch {}
  }

  async function upload(kind: 'avatar' | 'header', file: File) {
    try {
      // サーバ側は type パラメータを期待（kind は互換）
      const q = new URLSearchParams({ type: kind }).toString();
      const res = await apiUpload<{ ok: boolean; avatarUrl?: string; headerUrl?: string }>(`/api/user/profile/upload?${q}`, file);
      const bust = `?t=${Date.now()}`;
      const nextAvatar = res.avatarUrl ? (res.avatarUrl.includes('?') ? res.avatarUrl : res.avatarUrl + bust) : undefined;
      const nextHeader = res.headerUrl ? (res.headerUrl.includes('?') ? res.headerUrl : res.headerUrl + bust) : undefined;
      setProfile((p) => (p ? { ...p, ...(nextAvatar ? { avatarUrl: nextAvatar } : {}), ...(nextHeader ? { headerUrl: nextHeader } : {}) } : p));
      // /api/user/me を再フェッチしてグローバル状態を更新
      await refreshProfile();
      setMsg(kind === 'avatar' ? 'アイコンを更新しました' : 'ヘッダーを更新しました');
      setTimeout(() => setMsg(null), 2000);
    } catch {}
  }

  return (
    <main className="mx-auto max-w-4xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">プロフィール設定</h1>
      {msg && <div className="mb-3 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-gold-300">{msg}</div>}
      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">ヘッダー</h2>
        <div className="relative h-40 w-full bg-steam-iron-800 mb-2">
          {resolveUploadUrl(profile?.headerUrl) ? (
            <img src={resolveUploadUrl(profile?.headerUrl)} alt="header" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">NO Image</div>
          )}
          <label className="absolute right-3 bottom-3 cursor-pointer rounded bg-steam-iron-800/80 px-2 py-1 text-xs text-steam-gold-300 hover:bg-steam-iron-700">
            変更
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload('header', f); }} />
          </label>
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">アイコン</h2>
        <div className="flex items-center gap-3">
          <div className="h-20 w-20 overflow-hidden rounded-full border border-steam-iron-700 bg-steam-iron-800 flex items-center justify-center text-xs text-steam-iron-400">
            {resolveUploadUrl(profile?.avatarUrl) ? (
              <img src={resolveUploadUrl(profile?.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
            ) : (
              <span>未設定</span>
            )}
          </div>
          <label className="cursor-pointer rounded bg-steam-iron-800 px-2 py-1 text-xs text-steam-gold-300 hover:bg-steam-iron-700">
            画像を選択
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload('avatar', f); }} />
          </label>
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">表示名</h2>
        <div className="flex items-center gap-2">
          <input value={name} onChange={(e) => setName(e.target.value.slice(0, 50))} className="w-72 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-iron-100" placeholder="名前（50文字まで）" />
          <button onClick={saveName} className="rounded bg-steam-iron-800 px-3 py-2 text-xs text-steam-gold-300 hover:bg-steam-iron-700">保存</button>
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">プロフィール文</h2>
        <textarea value={bio} onChange={(e) => setBio(e.target.value.slice(0, 1000))} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-iron-100" rows={5} placeholder="プロフィール文（1000文字まで）" />
        <div className="mt-2 flex items-center justify-between text-xs text-steam-iron-300">
          <span>{bio.length}/1000</span>
          <button onClick={saveBio} className="rounded bg-steam-iron-800 px-3 py-2 text-xs text-steam-gold-300 hover:bg-steam-iron-700">保存</button>
        </div>
      </section>
    </main>
  );
}

