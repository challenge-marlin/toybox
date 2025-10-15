'use client';
import React from 'react';

export type Rank = 'GOLD' | 'SILVER' | 'BRONZE';
export type Rarity = 'SSR' | 'SR' | 'R' | 'N';

type Props = {
  titleText: string;
  rank?: Rank;
  rarity?: Rarity;
  colorCode?: string;
};

const RANK_COLORS: Record<Rank, string> = {
  GOLD: '#FFD700',
  SILVER: '#C0C0C0',
  BRONZE: '#CD7F32'
};

export default function TitleDisplay({ titleText, rank = 'BRONZE', rarity = 'N', colorCode }: Props) {
  const borderColor = colorCode || RANK_COLORS[rank];

  return (
    <div className="title-card-container">
      <div className="title-card" style={{ borderColor }}>
        <div className="title-rarity text-sm">{rarity}</div>
        <div className="title-text">{titleText}</div>
      </div>
      <style jsx>{`
        .title-card-container { display: flex; justify-content: center; }
        .title-card {
          background-color: rgba(26, 26, 26, 0.9);
          border: 2px solid ${borderColor};
          border-radius: 12px;
          padding: 16px 20px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.4), inset 0 0 10px rgba(0,0,0,0.3);
          min-width: 280px; max-width: 520px; text-align: center;
        }
        .title-rarity { letter-spacing: 0.1em; color: ${borderColor}; font-weight: 700; margin-bottom: 6px; }
        .title-text { font-size: 1.4rem; font-weight: 800; background: linear-gradient(180deg,#fff 0%,#ddd 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
      `}</style>
    </div>
  );
}


