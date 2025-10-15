'use client';
import React, { useEffect, useState } from 'react';

type Props = {
  result: 'win' | 'lose' | 'none';
  onFinished?: () => void;
  durationMs?: number;
};

const REEL = ['🍒','🍋','🔔','⭐','🍇','7️⃣'];

export default function SlotMachine({ result, onFinished, durationMs = 3000 }: Props) {
  const [r1, setR1] = useState(0);
  const [r2, setR2] = useState(0);
  const [r3, setR3] = useState(0);
  const [spinning, setSpinning] = useState(true);

  useEffect(() => {
    let t1: any, t2: any, t3: any, endT: any;
    const tick = 60; // ms
    t1 = setInterval(() => setR1((v) => (v + 1) % REEL.length), tick);
    t2 = setInterval(() => setR2((v) => (v + 1) % REEL.length), tick);
    t3 = setInterval(() => setR3((v) => (v + 1) % REEL.length), tick);

    endT = setTimeout(() => {
      // Stop reels with final result
      setSpinning(false);
      clearInterval(t1); clearInterval(t2); clearInterval(t3);
      if (result === 'win') {
        const seven = REEL.indexOf('7️⃣');
        setR1(seven); setR2(seven); setR3(seven);
      } else {
        // Ensure not 777
        const a = Math.floor(Math.random() * (REEL.length - 1));
        const b = Math.floor(Math.random() * (REEL.length - 1));
        const c = Math.floor(Math.random() * (REEL.length - 1));
        setR1(a); setR2(b); setR3(c);
      }
      setTimeout(() => onFinished && onFinished(), 600);
    }, durationMs);
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); clearTimeout(endT); };
  }, []);

  return (
    <div className="mx-auto w-full max-w-sm md:max-w-md select-none">
      <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-4 md:p-5">
        <div className="grid grid-cols-3 gap-3 text-center text-4xl md:text-5xl">
          <div className={`rounded bg-steam-iron-800 py-2 ${spinning ? 'animate-pulse' : ''}`}>{REEL[r1]}</div>
          <div className={`rounded bg-steam-iron-800 py-2 ${spinning ? 'animate-pulse' : ''}`}>{REEL[r2]}</div>
          <div className={`rounded bg-steam-iron-800 py-2 ${spinning ? 'animate-pulse' : ''}`}>{REEL[r3]}</div>
        </div>
        <div className="mt-4 text-center text-sm md:text-base text-steam-iron-200">スロット回転中…</div>
      </div>
    </div>
  );
}


