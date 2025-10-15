import React from 'react';

type Props = {
  open: boolean;
  onClose: () => void;
  result?: 'win' | 'lose' | 'none';
  rewardTitle?: string | null;
  rewardCardId?: string | null;
};

export default function ResultModal({ open, onClose, result, rewardTitle, rewardCardId }: Props) {
  if (!open) return null;
  const isWin = result === 'win';
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-md border border-steam-iron-700 bg-steam-iron-800 text-steam-gold-200 shadow-xl">
        <div className="border-b border-steam-iron-700 px-4 py-3 text-steam-gold-400">抽選結果</div>
        <div className="p-4 space-y-3">
          <div className={`text-xl font-semibold ${isWin ? 'text-steam-gold-300' : 'text-steam-brown-300'}`}>
            {isWin ? 'ジャックポット当選！' : '今回は見送り…'}
          </div>
          <div className="text-sm text-steam-iron-100">
            称号: <span className="text-steam-gold-200">{rewardTitle ?? '—'}</span>
          </div>
          <div className="text-sm text-steam-iron-100">
            カードID: <span className="text-steam-gold-200">{rewardCardId ?? '—'}</span>
          </div>
        </div>
        <div className="flex justify-end px-4 pb-4">
          <button onClick={onClose} className="rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600">
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
