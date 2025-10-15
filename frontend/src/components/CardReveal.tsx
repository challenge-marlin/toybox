'use client';
import React, { useState } from 'react';

type Props = {
  imageUrl?: string | null;
  cardName: string;
  rarity?: 'SSR' | 'SR' | 'R' | 'N';
  onClose?: () => void;
};

export default function CardReveal({ imageUrl, cardName, rarity = 'N', onClose }: Props) {
  const [show, setShow] = useState(true);
  const isEpic = rarity === 'SSR' || rarity === 'SR';

  return !show ? null : (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className={`rounded-md border p-3 shadow-xl ${isEpic ? 'border-yellow-500' : 'border-steam-iron-700'} bg-steam-iron-900`}>
        <div className="text-center text-steam-gold-200 mb-2">{rarity} 獲得！</div>
        <div className="w-[280px] h-[400px] bg-steam-iron-800 flex items-center justify-center overflow-hidden rounded">
          {imageUrl ? (
            <img src={imageUrl} alt={cardName} className="w-full h-full object-cover" />
          ) : (
            <div className="text-steam-iron-200">{cardName}</div>
          )}
        </div>
        <div className="mt-2 text-center text-steam-iron-100">{cardName}</div>
        <div className="text-center mt-3">
          <button className="rounded bg-steam-brown-500 px-4 py-2 text-white hover:bg-steam-brown-600" onClick={() => { setShow(false); onClose?.(); }}>
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}


