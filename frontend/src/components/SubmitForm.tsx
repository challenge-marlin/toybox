'use client';
import React, { useState } from 'react';
import { apiPost } from '../lib/api';
import SlotMachine from './SlotMachine';
import CardReveal from './CardReveal';

type SubmitPayload = {
  anonId: string;
  aim: string;
  steps: string[];
  frameType: string;
};

type SubmitResult = {
  jpResult: 'win' | 'lose' | 'none';
  probability: number;
  bonusCount: number;
  rewardTitle?: string;
  rewardCardId?: string;
  jackpotRecordedAt?: string | null;
};

export default function SubmitForm() {
  const [anonId, setAnonId] = useState('demo-anon');
  const [aim, setAim] = useState('');
  const [steps, setSteps] = useState(['', '', '']);
  const [frameType, setFrameType] = useState('default');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'card' | 'title' | 'slot' | 'done'>('idle');
  const [reveal, setReveal] = useState<{ imageUrl?: string | null; cardName: string; rarity?: 'SSR' | 'SR' | 'R' | 'N' } | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setPhase('idle');
    try {
      const payload: SubmitPayload = { anonId, aim, steps, frameType };
      try {
        const data = await apiPost<SubmitResult, SubmitPayload>(`/api/submit`, payload, { anonId });
        setResult(data);
        // 並列演出: カード→称号→スロット→完了
        setPhase('card');
        // カード演出はサーバ側の即時報酬に統合（ここでの追加生成はしない）
        await new Promise((r) => setTimeout(r, 800));
        setPhase('title');
        // 2) 称号獲得表示（ダミー画像）
        await new Promise((r) => setTimeout(r, 800));
        setPhase('slot');
        // 3) スロット（一日一回の結果を表示）
        await new Promise((r) => setTimeout(r, 2000));
        setPhase('done');
        // 4) 完了後にマイページへ戻る
        window.location.href = '/mypage';
      } catch (networkErr) {
        // バックエンドが停止中の場合のフォールバック（モック結果）
        const mock: SubmitResult = {
          jpResult: 'none',
          probability: 0.0,
          bonusCount: 0,
          rewardTitle: undefined,
          rewardCardId: undefined,
          jackpotRecordedAt: null
        };
        setResult(mock);
        setPhase('card');
        // バックエンド停止時のフォールバックでも追加生成は行わない
        await new Promise((r) => setTimeout(r, 800));
        setPhase('title');
        await new Promise((r) => setTimeout(r, 800));
        setPhase('slot');
        await new Promise((r) => setTimeout(r, 2000));
        setPhase('done');
        window.location.href = '/mypage';
      }
    } catch (err: any) {
      setError(err?.message ?? '送信に失敗しました');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="block text-sm text-steam-gold-300">匿名ID</label>
        <input className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" value={anonId} onChange={(e) => setAnonId(e.target.value)} />
      </div>
      <div>
        <label className="block text-sm text-steam-gold-300">ねらい（最大100字）</label>
        <textarea maxLength={100} className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" value={aim} onChange={(e) => setAim(e.target.value)} />
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {steps.map((s, i) => (
          <div key={i}>
            <label className="block text-sm text-steam-gold-300">手順 {i + 1}</label>
            <input className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" value={s} onChange={(e) => setSteps(Object.assign([...steps], { [i]: e.target.value }))} />
          </div>
        ))}
      </div>
      <div>
        <label className="block text-sm text-steam-gold-300">フレーム種別</label>
        <select className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" value={frameType} onChange={(e) => setFrameType(e.target.value)}>
          <option value="default">default</option>
          <option value="bronze">bronze</option>
          <option value="iron">iron</option>
          <option value="gold">gold</option>
        </select>
      </div>
      {error && <div className="text-red-400 text-sm">{error}</div>}
      <button disabled={loading} className="rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400 disabled:opacity-50">{loading ? '送信中…' : '提出する'}</button>
      {result && (
        <div className="mt-4 space-y-4">
          {/* カード獲得 */}
          {phase === 'card' && reveal && (
            <CardReveal imageUrl={reveal.imageUrl || undefined} cardName={reveal.cardName} rarity={reveal.rarity} onClose={() => setReveal(null)} />
          )}
          {/* 称号獲得 */}
          {phase === 'title' && (
            <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3 text-center">
              <div className="text-steam-gold-300 font-semibold">称号を取得しました！</div>
              <div className="mt-2 flex justify-center">
                <img src="/uploads/sample_2.svg" alt="dummy title" className="h-20 w-auto" />
              </div>
              <div className="mt-1 text-sm text-steam-iron-100">{result.rewardTitle ?? '新しい称号'}</div>
            </div>
          )}
          {/* スロット演出 */}
          {phase === 'slot' && (
            <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3">
              <div className="mb-2 text-center text-steam-iron-100">ジャックポット抽選（本日初投稿のみ対象）</div>
              <SlotMachine result={result.jpResult} />
              <div className="mt-2 text-center text-sm text-steam-iron-200">
                {result.jpResult === 'win' ? 'おめでとうございます！' : 'また明日チャレンジ！'}
              </div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}
