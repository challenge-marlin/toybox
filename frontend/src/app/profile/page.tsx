"use client";
import React, { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPatch, apiUpload } from '../../lib/api';
import { resolveUploadUrl } from '../../lib/assets';
import { useToast } from '../../components/ToastProvider';
import { UpdateBioSchema, UpdateDisplayNameSchema } from '../../validation/user';
import { useRouter } from 'next/navigation';
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
  const toast = useToast();
  const router = useRouter();
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [headerFile, setHeaderFile] = useState<File | null>(null);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState<string | null>(null);
  const [headerPreviewUrl, setHeaderPreviewUrl] = useState<string | null>(null);

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

  // use shared resolver from lib/assets

  async function onSaveAll() {
    setSaving(true);
    setMsg(null);
    try {
      try {
        UpdateDisplayNameSchema.parse({ displayName: name });
        UpdateBioSchema.parse({ bio });
      } catch (e) {
        toast.error('入力値が不正です（表示名は1〜50文字、プロフィール文は最大1000文字）');
        setSaving(false);
        return;
      }
      // 画像アップロード（選択されている場合のみ）
      if (headerFile) {
        await apiUpload<{ ok: boolean; headerUrl?: string }>(`/api/user/profile/upload?${new URLSearchParams({ type: 'header' })}`, headerFile);
      }
      if (avatarFile) {
        await apiUpload<{ ok: boolean; avatarUrl?: string }>(`/api/user/profile/upload?${new URLSearchParams({ type: 'avatar' })}`, avatarFile);
      }
      // テキスト一括保存
      await apiPatch<UserMe>(`/api/user/profile`, { displayName: name, bio });
      setMsg('保存しました。マイページへ移動します…');
      toast.success('プロフィールを保存しました');
      try { localStorage.setItem('toybox_mypage_force_reload', '1'); } catch {}
      router.push('/mypage');
    } catch {
      setMsg('保存に失敗しました');
      toast.error('プロフィールの保存に失敗しました');
    } finally {
      setSaving(false);
    }
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

  // ファイル選択時のプレビュー管理
  function onSelectHeader(file?: File) {
    if (!file) return;
    try { if (headerPreviewUrl) URL.revokeObjectURL(headerPreviewUrl); } catch {}
    setHeaderFile(file);
    setHeaderPreviewUrl(URL.createObjectURL(file));
  }
  function onSelectAvatar(file?: File) {
    if (!file) return;
    try { if (avatarPreviewUrl) URL.revokeObjectURL(avatarPreviewUrl); } catch {}
    setAvatarFile(file);
    setAvatarPreviewUrl(URL.createObjectURL(file));
  }

  return (
    <main className="mx-auto max-w-4xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">プロフィール設定</h1>
      {msg && <div className="mb-3 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-gold-300">{msg}</div>}
      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">ヘッダー</h2>
        <div className="relative h-40 w-full bg-steam-iron-800 mb-2">
          {(headerPreviewUrl || resolveUploadUrl(profile?.headerUrl)) ? (
            <img src={headerPreviewUrl || resolveUploadUrl(profile?.headerUrl)} alt="header" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">NO Image</div>
          )}
          <label className="absolute right-3 bottom-3 cursor-pointer rounded bg-steam-iron-800/80 px-2 py-1 text-xs text-steam-gold-300 hover:bg-steam-iron-700">
            変更
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; onSelectHeader(f); }} />
          </label>
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">アイコン</h2>
        <div className="flex items-center gap-3">
          <div className="h-20 w-20 overflow-hidden rounded-full border border-steam-iron-700 bg-steam-iron-800 flex items-center justify-center text-xs text-steam-iron-400">
            {(avatarPreviewUrl || resolveUploadUrl(profile?.avatarUrl)) ? (
              <img src={avatarPreviewUrl || resolveUploadUrl(profile?.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
            ) : (
              <span>未設定</span>
            )}
          </div>
          <label className="cursor-pointer rounded bg-steam-iron-800 px-2 py-1 text-xs text-steam-gold-300 hover:bg-steam-iron-700">
            画像を選択
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; onSelectAvatar(f); }} />
          </label>
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">表示名</h2>
        <div className="flex items-center gap-2">
          <input value={name} onChange={(e) => setName(e.target.value.slice(0, 50))} className="w-72 rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-iron-100" placeholder="名前（50文字まで）" />
        </div>
      </section>

      <section className="mb-6 rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
        <h2 className="mb-2 text-steam-gold-300 font-semibold">プロフィール文</h2>
        <textarea value={bio} onChange={(e) => setBio(e.target.value.slice(0, 1000))} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2 text-sm text-steam-iron-100" rows={5} placeholder="プロフィール文（1000文字まで）" />
        <div className="mt-2 flex items-center justify-between text-xs text-steam-iron-300">
          <span>{bio.length}/1000</span>
        </div>
      </section>

      <div className="mb-10" />
      <div className="sticky bottom-4 flex justify-center">
        <button
          onClick={onSaveAll}
          disabled={saving}
          className="rounded bg-steam-gold-500 text-black font-semibold px-8 py-3 shadow-lg hover:bg-steam-gold-400 disabled:opacity-60"
        >
          {saving ? '保存中…' : '変更を保存してマイページへ'}
        </button>
      </div>
    </main>
  );
}

