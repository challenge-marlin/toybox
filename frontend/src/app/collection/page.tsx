'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../../lib/api';

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
  const [sortKey, setSortKey] = useState<'rarity' | 'attribute' | 'obtained'>('rarity');

  useEffect(() => {
    (async () => {
      try {
        const s = await apiGet<Summary>('/api/cards/summary');
        setSummary(s);
        const res = await apiGet<{ ok: boolean; entries: Entry[] }>('/api/cards/me');
        setEntries(res.entries);
      } catch (e) {
        try { window.location.href = '/login?next=/collection'; } catch {}
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    return entries.filter(e => (tab === 'character' ? e.meta?.card_type === 'Character' : e.meta?.card_type === 'Effect'));
  }, [entries, tab]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      if (sortKey === 'obtained') return (new Date(b.obtainedAt || 0).getTime()) - (new Date(a.obtainedAt || 0).getTime());
      if (sortKey === 'attribute') return (a.meta?.attribute || '').localeCompare(b.meta?.attribute || '');
      const order = { 'SSR': 4, 'SR': 3, 'R': 2, 'N': 1 } as any;
      return (order[b.meta?.rarity || 'N'] || 0) - (order[a.meta?.rarity || 'N'] || 0);
    });
  }, [filtered, sortKey]);

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
        <select className="rounded border border-steAM-iron-700 bg-steam-iron-900 px-2 py-1" value={sortKey} onChange={e => setSortKey(e.target.value as any)}>
          <option value="rarity">レアリティ順</option>
          <option value="attribute">属性順</option>
          <option value="obtained">入手日（新しい順）</option>
        </select>
      </div>

      {tab === 'character' ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {sorted.map(e => (
            <div key={e.id} className="rounded border border-steam-iron-700 bg-steam-iron-900 p-2">
              <div className="aspect-[2/3] bg-steam-iron-800 rounded mb-2 overflow-hidden">
                {e.meta?.image_url ? <img src={e.meta.image_url} alt={e.meta.card_name} className="w-full h-full object-cover" /> : null}
              </div>
              <div className="text-xs text-steam-iron-200">{e.meta?.rarity ?? '-'}</div>
              <div className="text-sm text-steam-gold-200">{e.meta?.card_name ?? e.id}</div>
              <div className="text-xs text-steam-iron-300">{e.meta?.attribute ?? '-'}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {sorted.map(e => (
            <div key={e.id} className="rounded border border-steam-iron-700 bg-steam-iron-900 p-2 flex items-center justify-between">
              <div>
                <div className="text-steam-gold-200">{e.meta?.card_name ?? e.id}</div>
                <div className="text-xs text-steam-iron-300">{e.obtainedAt ? new Date(e.obtainedAt).toLocaleString() : ''}</div>
              </div>
              <div className="text-xs text-steam-iron-200">{e.meta?.image_url ? '画像あり' : ''}</div>
            </div>
          ))}
        </div>
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


