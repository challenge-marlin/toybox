"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiGet, apiPost } from '../lib/api';

export default function Page() {
  const [hasSession, setHasSession] = useState<boolean>(false);
  const [showSplash, setShowSplash] = useState<boolean>(false);
  const [splashFade, setSplashFade] = useState<boolean>(false);
  const router = useRouter();

  useEffect(() => {
    (async () => {
      try {
        const me = await apiGet<{ ok: boolean; user: { anonId: string } | null }>(`/api/auth/me`);
        setHasSession(!!me && (me as any).ok && !!(me as any).user);
      } catch {
        setHasSession(false);
      }
    })();
  }, []);

  // このページ滞在中は縦スクロールを無効化
  useEffect(() => {
    const prevBodyOverflow = typeof document !== 'undefined' ? document.body.style.overflow : '';
    const prevHtmlOverflow = typeof document !== 'undefined' ? document.documentElement.style.overflow : '';
    if (typeof document !== 'undefined') {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    }
    return () => {
      if (typeof document !== 'undefined') {
        document.body.style.overflow = prevBodyOverflow;
        document.documentElement.style.overflow = prevHtmlOverflow;
      }
    };
  }, []);

  // ページ読み込み毎にスプラッシュ（ローディング）を表示し、最後にフェードアウト
  useEffect(() => {
    setShowSplash(true);
    const fadeT = setTimeout(() => setSplashFade(true), 1200); // 最後の0.3秒でフェード
    const hideT = setTimeout(() => {
      setShowSplash(false);
      setSplashFade(false);
    }, 1500);
    return () => {
      clearTimeout(fadeT);
      clearTimeout(hideT);
    };
  }, []);

  // 匿名IDの生成は廃止
  async function onLogout() {
    try { await apiPost(`/api/auth/logout`, {} as any); } catch {}
    setHasSession(false);
    try { router.push('/'); } catch {}
  }

  return (
    <div className="relative min-h-[calc(100dvh-56px)] md:min-h-[calc(100dvh-64px)] overflow-hidden">
      {showSplash ? (
        <div
          className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity duration-300 ease-out ${splashFade ? 'opacity-0' : 'opacity-100'}`}
          style={{ backgroundColor: '#FFC626' }}
        >
          <div className="text-center">
            <img src="/hero/nowloading.gif" alt="Now Loading" className="mx-auto h-24 w-auto md:h-32" />
            <div className="mt-2 text-[12px] md:text-sm text-[#5c3a21]">Nowloading...</div>
          </div>
        </div>
      ) : null}
      <video
        className="fixed inset-0 z-0 h-full w-full object-cover object-center"
        src="/hero/background.mp4"
        poster="/hero/background.png"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        aria-hidden="true"
      />
      <main className="relative z-10 mx-auto max-w-6xl px-6 py-0 overflow-hidden">
        {/* Hero */}
        <section
          className="relative overflow-hidden rounded-lg bg-center bg-cover min-h-full"
        >
          <div className="relative p-6 md:p-8 h-full flex items-start">
            {hasSession ? (
              <div className="relative z-20 w-full text-center">
                <img src="/hero/toybox-title.png" alt="TOYBOX ロゴ" className="mx-auto h-28 w-auto md:h-36 lg:h-40" />
                <div className="mt-6 flex flex-col items-center gap-3 justify-center">
                  <Link href="/mypage" className="rounded bg-steam-gold-500 px-6 py-3 text-black text-base md:text-lg hover:bg-steam-gold-400">
                    マイページへ
                  </Link>
                  <button onClick={onLogout} className="rounded border border-steam-gold-500 px-6 py-3 text-steam-gold-200 text-base md:text-lg hover:bg-steam-iron-800">
                    ログアウト
                  </button>
                </div>
                <div className="mt-6">
                  <img src="/hero/mio.png" alt="綾鳥みお" className="mio-float pointer-events-none mx-auto block h-[800px] max-h-[60vh] w-auto select-none" />
                </div>
              </div>
            ) : (
              <>
                <div className="relative z-20 w-full text-center">
                  <img src="/hero/toybox-title.png" alt="TOYBOX ロゴ" className="mx-auto h-28 w-auto md:h-36 lg:h-40" />
                  <p className="mt-4 mx-auto max-w-2xl text-steam-iron-100 md:text-lg">
                    毎日の“お題”に挑戦して、コレクションを増やそう。
                  </p>
                  <div className="mt-6 flex flex-col items-center gap-3 justify-center">
                    <Link href="/login" className="rounded bg-steam-gold-500 px-6 py-3 text-black text-base md:text-lg hover:bg-steam-gold-400">
                      ログイン
                    </Link>
                    <Link href="/signup" className="rounded border border-steam-gold-500 px-6 py-3 text-steam-gold-200 text-base md:text-lg hover:bg-steAM-iron-800">
                      アカウント作成
                    </Link>
                  </div>
                  <div className="mt-6">
                    <img src="/hero/mio.png" alt="綾鳥みお" className="mio-float pointer-events-none mx-auto block h-[800px] max-h-[60vh] w-auto select-none" />
                  </div>
                </div>
                {/* Feature cards overlayed above mio.png to avoid scroll */}
                <div className="absolute inset-x-0 bottom-32 z-30 flex justify-center">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3 w-full max-w-6xl px-6">
                    <div className="rounded-lg border border-steam-iron-800 bg-steam-iron-900/90 p-4">
                      <div className="mb-2 text-steam-gold-300 font-semibold">続けるほど当たりやすい</div>
                      <p className="text-sm text-steam-iron-200">毎日の提出でボーナスが蓄積。未当選が続くほど確率が少しずつ上がります。</p>
                    </div>
                    <div className="rounded-lg border border-steam-iron-800 bg-steam-iron-900/90 p-4">
                      <div className="mb-2 text-steam-gold-300 font-semibold">称号とカードをコレクション</div>
                      <p className="text-sm text-steam-iron-200">当選すると限定称号やカードを獲得。プロフィールで自慢できます。</p>
                    </div>
                    <div className="rounded-lg border border-steam-iron-800 bg-steam-iron-900/90 p-4">
                      <div className="mb-2 text-steam-gold-300 font-semibold">コミュニティで刺激を受ける</div>
                      <p className="text-sm text-steam-iron-200">他の参加者の取り組みからヒントを得て、継続のモチベーションに。</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
