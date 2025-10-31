'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../../lib/api';
import { resolveUploadUrl } from '../../lib/assets';
const FRAME_URL = '/uploads/cards/frame.png';

type Entry = {
  id: string;
  obtainedAt: string | null;
  meta: {
    card_id: string;
    card_type: 'Character' | 'Effect';
    card_name: string;
    rarity?: 'SSR' | 'SR' | 'R' | 'N';
    attribute?: string;
    image_url?: string;
  } | null;
};

type Summary = {
  ok: boolean;
  total: number;
  rarity: { SSR: number; SR: number; R: number; N: number };
  byAttr: Record<string, number>;
};

export default function CollectionPage() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [tab, setTab] = useState<'character' | 'effect'>('character');

  function candidatesFor(meta?: Entry['meta']): string[] {
    if (!meta) return [];
    const primary = resolveUploadUrl(meta.image_url) || (resolveUploadUrl(`/uploads/cards/${meta.card_id}.png`) as string);
    return [primary];
  }

  function CardImage({ meta }: { meta?: Entry['meta'] }) {
    const srcs = candidatesFor(meta);
    if (srcs.length === 0) return null;
    const src = srcs[0];
    return (
      <img
        src={src}
        alt={meta?.card_name || ''}
        className="absolute inset-0 w-full h-full object-contain"
        style={{ transform: 'scale(0.97)', transformOrigin: 'center' }}
      />
    );
  }

  useEffect(() => {
    (async () => {
      try {
        const [s, res] = await Promise.all([
          apiGet<Summary>('/api/cards/summary'),
          apiGet<{ ok: boolean; entries: Entry[] }>('/api/cards/me')
        ]);
        setSummary(s);
        setEntries(res.entries);
      } catch (e) {
        try { window.location.href = '/login?next=/collection'; } catch {}
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    return entries.filter(e => {
      const type = e.meta?.card_type;
      if (tab === 'character') return type === 'Character' && /^C/i.test(e.id);
      return type === 'Effect' && /^E/i.test(e.id);
    });
  }, [entries, tab]);

  const ordered = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const ta = a.obtainedAt ? new Date(a.obtainedAt).getTime() : 0;
      const tb = b.obtainedAt ? new Date(b.obtainedAt).getTime() : 0;
      return tb - ta; // 入手日（新しい順）
    });
  }, [filtered]);

  function CardTile({ e }: { e: Entry }) {
    return (
      <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-2">
        <div className="relative aspect-[2/3] bg-steam-iron-800 rounded mb-2 overflow-hidden">
          <CardImage meta={e.meta || undefined} />
          <img src={FRAME_URL} alt="" aria-hidden="true" className="absolute inset-0 w-full h-full object-contain pointer-events-none" style={{ transform: 'scale(1.02)', transformOrigin: 'center' }} />
        </div>
        <div className="text-xs text-steam-iron-200">{e.meta?.rarity ?? '-'}</div>
        <div className="text-sm text-steam-gold-200">{e.meta?.card_name ?? e.id}</div>
        {e.meta?.card_type === 'Character' ? (
          <div className="text-xs text-steam-iron-300">{e.meta?.attribute ?? '-'}</div>
        ) : null}
      </div>
    );
  }

  function CardGrid({ items }: { items: Entry[] }) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {items.map(e => (
          <CardTile key={e.id} e={e} />
        ))}
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-6xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">コレクション</h1>
      {summary && (
        <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat label="総数" value={summary.total} />
          <Stat label="SSR" value={summary.rarity.SSR} />
          <Stat label="SR" value={summary.rarity.SR} />
          <Stat label="R" value={summary.rarity.R} />
          <Stat label="N" value={summary.rarity.N} />
        </div>
      )}

      <div className="mb-3 flex items-center gap-3">
        <div className="inline-flex rounded border border-steam-iron-700">
          <button className={`px-3 py-1 ${tab === 'character' ? 'bg-steam-iron-700 text-steam-gold-200' : ''}`} onClick={() => setTab('character')}>キャラクター</button>
          <button className={`px-3 py-1 ${tab === 'effect' ? 'bg-steam-iron-700 text-steam-gold-200' : ''}`} onClick={() => setTab('effect')}>効果</button>
        </div>
      </div>

      {ordered.length === 0 ? (
        <div className="text-sm text-steam-iron-300">カードがありません。</div>
      ) : (
        <CardGrid items={ordered} />
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-3 text-center">
      <div className="text-xs text-steam-iron-300">{label}</div>
      <div className="text-xl text-steam-gold-200">{value}</div>
    </div>
  );
}


