import fs from 'node:fs/promises';
import path from 'node:path';

export type CardType = 'Character' | 'Effect';
export type Rarity = 'N' | 'R' | 'SR' | 'SSR';

export interface CardMasterRow {
  card_id: string;
  card_type: CardType;
  card_name: string;
  rarity: Rarity | '-';
  rarity_rate: number | '-';
  attribute: '木' | '火' | '土' | '金' | '水' | '-' | string;
  base_atk: number | '-';
  base_def: number | '-';
  effect_category: string | '-';
  effect_target: string | '-';
  effect_value: string | number | '-';
  duration_turn: number | '-';
  special_effect_code: string | '-';
  initial_deck_count: number | '-';
  image_url: string | '-';
}

export interface PublicCard {
  card_id: string;
  card_type: CardType;
  card_name: string;
  rarity?: Rarity;
  attribute?: string;
  image_url?: string | null;
}

const DEFAULT_RARITY_RATES: Record<Rarity, number> = {
  SSR: 0.01,
  SR: 0.04,
  R: 0.20,
  N: 0.75
};

let _cache: CardMasterRow[] | null = null;

export async function loadCardMaster(): Promise<CardMasterRow[]> {
  if (_cache) return _cache;
  const tsvPath = process.env.CARD_MASTER_TSV || path.resolve(process.cwd(), 'src', 'data', 'card_master.small.tsv');
  let raw = '';
  try {
    raw = await fs.readFile(tsvPath, 'utf-8');
  } catch {
    raw = DEFAULT_TSV_FALLBACK.trim();
  }
  const rows = parseTsv(raw);
  _cache = rows;
  return rows;
}

export function parseTsv(tsv: string): CardMasterRow[] {
  const lines = tsv.split(/\r?\n/).filter(l => l.trim().length > 0);
  if (lines.length === 0) return [];
  const header = lines[0].split('\t');
  const idx = (name: string) => header.indexOf(name);
  const _rows: CardMasterRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split('\t');
    const get = (name: string) => cols[idx(name)] ?? '';
    const rarity = (get('rarity') || '-') as any;
    const rarity_rate_raw = get('rarity_rate');
    const rarity_rate = rarity_rate_raw === '-' ? '-' : Number(rarity_rate_raw);
    const base_atk_raw = get('base_atk'); const base_def_raw = get('base_def');
    const duration_raw = get('duration_turn'); const initial_raw = get('initial_deck_count');
    _rows.push({
      card_id: get('card_id'),
      card_type: (get('card_type') as any),
      card_name: get('card_name'),
      rarity,
      rarity_rate,
      attribute: (get('attribute') || '-') as any,
      base_atk: base_atk_raw === '-' ? '-' : Number(base_atk_raw),
      base_def: base_def_raw === '-' ? '-' : Number(base_def_raw),
      effect_category: get('effect_category') || '-',
      effect_target: get('effect_target') || '-',
      effect_value: (() => {
        const v = get('effect_value');
        if (v === '-' || v === '') return '-';
        const n = Number(v);
        return Number.isNaN(n) ? v : n;
      })(),
      duration_turn: duration_raw === '-' ? '-' : Number(duration_raw),
      special_effect_code: get('special_effect_code') || '-',
      initial_deck_count: initial_raw === '-' ? '-' : Number(initial_raw),
      image_url: get('image_url') || '-',
    });
  }
  return _rows;
}

export async function drawCharacter(master?: CardMasterRow[]): Promise<CardMasterRow | null> {
  const m = master || await loadCardMaster();
  const byRarity = {
    SSR: m.filter(r => r.card_type === 'Character' && r.rarity === 'SSR'),
    SR:  m.filter(r => r.card_type === 'Character' && r.rarity === 'SR'),
    R:   m.filter(r => r.card_type === 'Character' && r.rarity === 'R'),
    N:   m.filter(r => r.card_type === 'Character' && r.rarity === 'N'),
  } as const;
  const rates = DEFAULT_RARITY_RATES;
  const pickedRarity = weightedPick([
    ['SSR', rates.SSR],
    ['SR',  rates.SR],
    ['R',   rates.R],
    ['N',   rates.N],
  ]) as Rarity;
  const pool = byRarity[pickedRarity];
  if (!pool?.length) {
    const any = m.filter(r => r.card_type === 'Character');
    return any.length ? any[Math.floor(Math.random() * any.length)] : null;
  }
  return pool[Math.floor(Math.random() * pool.length)];
}

export async function drawEffect(master?: CardMasterRow[]): Promise<CardMasterRow | null> {
  const m = master || await loadCardMaster();
  const effects = m.filter(r => r.card_type === 'Effect');
  if (!effects.length) return null;
  return effects[Math.floor(Math.random() * effects.length)];
}

export function toPublicCard(row: CardMasterRow): PublicCard {
  return {
    card_id: row.card_id,
    card_type: row.card_type,
    card_name: row.card_name,
    rarity: row.rarity && row.rarity !== '-' ? (row.rarity as any) : undefined,
    attribute: row.attribute && row.attribute !== '-' ? row.attribute : undefined,
    image_url: row.image_url && row.image_url !== '-' ? row.image_url : undefined,
  };
}

function weightedPick(items: [string, number][]): string {
  const total = items.reduce((s, [, w]) => s + w, 0);
  const r = Math.random() * total;
  let acc = 0;
  for (const [key, w] of items) {
    acc += w;
    if (r <= acc) return key;
  }
  return items[items.length - 1][0];
}

const DEFAULT_TSV_FALLBACK = `
card_id	card_type	card_name	rarity	rarity_rate	attribute	base_atk	base_def	effect_category	effect_target	effect_value	duration_turn	special_effect_code	initial_deck_count	image_url
C001	Character	見習いプランナー	N	0.75	木	100	100	-	-	-	-	-	1	-
C006	Character	タスク・レンジャー	R	0.20	木	150	150	-	-	-	-	-	1	-
C101	Character	スチーム・アーキテクト	SR	0.04	金	250	250	-	-	-	-	-	1	-
C201	Character	ネビュラの王	SSR	0.01	水	400	400	-	-	-	-	-	1	-
C002	Character	駆け出しインフルエンサー	N	0.75	火	100	100	-	-	-	-	-	1	-
C007	Character	炎舞のソーシャルナイト	R	0.20	火	150	150	-	-	-	-	-	1	-
C102	Character	歯車の守護者	SR	0.04	土	250	250	-	-	-	-	-	1	-
C202	Character	蒸気の覇者	SSR	0.01	金	400	400	-	-	-	-	-	1	-
E001	Effect	【スプリントブースト】	-	-	-	-	-	強化	Self_ATK	50	2	-	1	-
E002	Effect	【データガード】	-	-	-	-	-	防御	Self_DEF	50	2	-	1	-
E003	Effect	【クリーンヒット】	-	-	-	-	-	攻撃	Opponent_HP	-100	-	-	1	-
E004	Effect	【緊急回復】	-	-	-	-	-	回復	Self_HP	200	-	-	1	-
`.trim();

