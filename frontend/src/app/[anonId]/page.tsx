'use client';
import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { API_BASE, apiGet } from '../../lib/api';
import { getAnonId } from '../../lib/auth';

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
  const [profile, setProfile] = useState<PublicProfile | null>(null);

  useEffect(() => {
    if (!anonId) return;
    (async () => {
      try {
        const p = await apiGet<PublicProfile>(`/api/user/profile/${encodeURIComponent(anonId)}`);
        setProfile(p);
      } catch { setProfile(null); }
    })();
  }, [anonId]);

  function resolveUploadUrl(u?: string | null): string | undefined {
    if (!u) return undefined;
    if (u.startsWith('/uploads/')) return `${API_BASE}${u}`;
    return u;
  }

  return (
    <main className="mx-auto max-w-6xl p-4">
      <h1 className="mb-3 text-2xl font-bold text-steam-gold-300">プロフィール</h1>
      {profile ? (
        <section className="mb-6 overflow-hidden rounded border border-steam-iron-700 bg-steam-iron-900">
          <div className="relative h-40 w-full bg-steam-iron-800">
            {resolveUploadUrl(profile.headerUrl) ? (
              <img src={resolveUploadUrl(profile.headerUrl)} alt="header" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-sm">NO Image</div>
            )}
          </div>
          <div className="flex items-start gap-4 p-3">
            <div className="relative -mt-10 h-20 w-20 flex-shrink-0 overflow-hidden rounded-full border-2 border-steam-iron-700 bg-steam-iron-800">
              {resolveUploadUrl(profile.avatarUrl) ? (
                <img src={resolveUploadUrl(profile.avatarUrl)} alt="avatar" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-steam-iron-400 text-xs">未設定</div>
              )}
            </div>
            <div className="flex-1">
              <div className="text-steam-iron-100 text-lg font-semibold">{profile.displayName || profile.anonId}</div>
              <div className="mt-1 text-sm text-steam-iron-300">@{profile.anonId}</div>
              <div className="text-sm text-steam-gold-300">称号: {profile.activeTitle || '—'}</div>
              {profile.activeTitleUntil && (
                <div className="text-xs text-steam-iron-300">有効期限: {new Date(profile.activeTitleUntil).toLocaleDateString()}</div>
              )}
            </div>
          </div>
          {profile.bio ? (
            <div className="px-3 pb-3 text-sm leading-relaxed text-steam-iron-200 whitespace-pre-wrap">
              {profile.bio}
            </div>
          ) : null}
        </section>
      ) : (
        <div className="mb-6 h-20 animate-pulse rounded border border-steam-iron-800 bg-steam-iron-900" />
      )}
    </main>
  );
}



