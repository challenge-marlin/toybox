import { SubmissionModel } from '../../models/Submission.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import type { UserMeta } from '../../models/UserMeta.js';
import { enqueueNotification } from '../queue/notificationQueue.js';
import { logger } from '../utils/logger.js';
import { loadCardMaster, drawCharacter, drawEffect, toPublicCard } from '../data/cardMaster.js';
import { startOfJstDay, endOfJstDay } from '../utils/time.js';

// 抽選確率計算: P_final = min(0.008 + 0.002 * k, 0.05)
export function calculateFinalProbability(consecutiveLoses: number): number {
  const k = Math.max(0, Math.floor(consecutiveLoses || 0));
  const p = 0.008 + 0.002 * k;
  return Math.min(p, 0.05);
}

// 1日1回提出チェック用: 同一 anonId の当日提出があるか
async function hasSubmittedToday(anonId: string): Promise<boolean> {
  const now = new Date();
  const start = startOfJstDay(now);
  const end = endOfJstDay(now);
  const count = await SubmissionModel.countDocuments({
    submitterAnonId: anonId,
    createdAt: { $gte: start, $lte: end }
  });
  return count > 0;
}

function drawWithProbability(prob: number): boolean {
  const r = Math.random();
  return r < prob;
}

// 即時報酬: ランダム称号（7日）とカード1枚付与
export async function grantImmediateRewards(user: UserMeta, opts?: { boostRarity?: boolean }): Promise<{ user: UserMeta; title: string; cardId: string; cardMeta?: { card_id: string; card_name: string; rarity?: string; image_url?: string | null } }> {
  const titles = [
    '蒸気の旅人',
    '真鍮の探究者',
    '歯車の達人',
    '工房の匠',
    '鉄と蒸気の詩人'
  ];
  const chosen = titles[Math.floor(Math.random() * titles.length)];
  const now = new Date();
  const until = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  // マスターからカードを抽選（キャラクター/エフェクトを50%で選択。なければフォールバックID）
  let chosenCardId = `card_${now.getTime()}`;
  let cardMeta: { card_id: string; card_name: string; rarity?: string; image_url?: string | null } | undefined;
  try {
    const master = await loadCardMaster();
    // まずカードタイプを50/50で選択
    const pickEffectType = Math.random() < 0.5;
    let picked = null as any;
    if (opts?.boostRarity) {
      // ゲーム投稿時は SSR/SR のレアリティ抽選確率を +1% ずつ上げる（合計は N から減算）
      const base = { SSR: 0.01, SR: 0.04, R: 0.20, N: 0.75 };
      const boost = 0.01;
      const rates = { SSR: base.SSR + boost, SR: base.SR + boost, R: base.R, N: 0 } as { SSR: number; SR: number; R: number; N: number };
      rates.N = Math.max(0, 1 - (rates.SSR + rates.SR + rates.R));
      type RKey = 'SSR' | 'SR' | 'R' | 'N';

      const inEffectRange = (id: string) => /^E(10[1-9]|11[0-9]|12[0-9]|13[0-6])$/.test(id);
      const poolByRarity = (type: 'Character' | 'Effect') => ({
        SSR: master.filter(r => r.card_type === type && r.rarity === 'SSR' && (type === 'Character' || inEffectRange(r.card_id))),
        SR:  master.filter(r => r.card_type === type && r.rarity === 'SR'  && (type === 'Character' || inEffectRange(r.card_id))),
        R:   master.filter(r => r.card_type === type && r.rarity === 'R'   && (type === 'Character' || inEffectRange(r.card_id))),
        N:   master.filter(r => r.card_type === type && r.rarity === 'N'   && (type === 'Character' || inEffectRange(r.card_id))),
      } as const);

      const byRarity = poolByRarity(pickEffectType ? 'Effect' : 'Character');
      const items: [RKey, number][] = [['SSR', rates.SSR], ['SR', rates.SR], ['R', rates.R], ['N', rates.N]];
      const total = items.reduce((s, [, w]) => s + w, 0);
      let r = Math.random() * total;
      let selected: RKey = 'N';
      for (const [k, w] of items) { r -= w; if (r <= 0) { selected = k; break; } }
      const pool = byRarity[selected as RKey];
      picked = pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
      if (!picked) {
        const any = master.filter(r => r.card_type === (pickEffectType ? 'Effect' : 'Character'))
          .filter(r => !pickEffectType || inEffectRange(r.card_id));
        picked = any.length ? any[Math.floor(Math.random() * any.length)] : null;
      }
    } else {
      if (pickEffectType) {
        const inEffectRange = (id: string) => /^E(10[1-9]|11[0-9]|12[0-9]|13[0-6])$/.test(id);
        const effects = master.filter(r => r.card_type === 'Effect' && inEffectRange(r.card_id));
        picked = effects.length ? effects[Math.floor(Math.random() * effects.length)] : null;
      } else {
        picked = await drawCharacter(master);
      }
    }
    if (picked) {
      chosenCardId = picked.card_id;
      const pub = toPublicCard(picked);
      cardMeta = {
        card_id: pub.card_id,
        card_name: pub.card_name,
        rarity: pub.rarity,
        image_url: pub.image_url ?? undefined
      };
    }
  } catch {}

  user.activeTitle = chosen;
  user.activeTitleUntil = until;
  user.cardsAlbum = [...(user.cardsAlbum || []), { id: chosenCardId, obtainedAt: now }];

  await user.save();
  logger.info('reward.granted', { anonId: user.anonId, title: chosen, cardId: chosenCardId });
  return { user, title: chosen, cardId: chosenCardId, cardMeta };
}

// 提出後の全処理
export interface SubmissionInput {
  submitterAnonId: string;
  aim: string;
  steps: string[];
  frameType: string;
  imageUrl?: string; // 画像アップロード後の相対URL（/uploads/...）
  videoUrl?: string; // 動画アップロード後の相対URL（/uploads/...）
  gameUrl?: string;  // 展開済みゲームの index.html への相対URL（/uploads/...）
}

export interface SubmissionResult {
  jpResult: 'none';
  probability: number;
  bonusCount: number; // 更新後の lotteryBonusCount
  rewardTitle?: string;
  rewardCardId?: string;
  rewardCard?: { card_id: string; card_name: string; rarity?: 'SSR' | 'SR' | 'R' | 'N'; image_url?: string | null };
  jackpotRecordedAt?: string | null;
}

export async function handleSubmissionAndLottery(input: SubmissionInput): Promise<SubmissionResult> {
  const { submitterAnonId } = input;
  const alreadyToday = await hasSubmittedToday(submitterAnonId);

  // 同時多発（短時間の二重送信）対策: 直近10秒以内に同一内容の提出が存在する場合はスキップ
  // 画像提出は imageUrl が一致、テキスト提出は aim/steps/frameType が一致するものを重複とみなす
  try {
    const tenSecondsAgo = new Date(Date.now() - 10_000);
    const dup = await SubmissionModel.findOne({
      submitterAnonId,
      createdAt: { $gte: tenSecondsAgo },
      ...(input.imageUrl || input.gameUrl
        ? { $or: [
            input.imageUrl ? { imageUrl: input.imageUrl } : {},
            input.gameUrl ? { gameUrl: input.gameUrl } : {}
          ] }
        : { aim: input.aim, steps: input.steps, frameType: input.frameType })
    }).lean();
    if (dup) {
      logger.info('submit.duplicate_skipped', { anonId: submitterAnonId });
      // 既存ユーザメタ取得し、現在のボーナス回数を返す
      const user = (await UserMetaModel.findOne({ anonId: submitterAnonId })) || (await UserMetaModel.create({ anonId: submitterAnonId, lotteryBonusCount: 0, cardsAlbum: [] }));
      return { jpResult: 'none', probability: 0, bonusCount: user.lotteryBonusCount };
    }
  } catch {}

  // ユーザメタ取得/作成
  const user = (await UserMetaModel.findOne({ anonId: submitterAnonId })) ||
    (await UserMetaModel.create({ anonId: submitterAnonId, lotteryBonusCount: 0, cardsAlbum: [] }));

  // 提出を保存（仮: 結果は後で反映）
  const submission = await SubmissionModel.create({
    submitterAnonId: input.submitterAnonId,
    aim: input.aim,
    steps: input.steps,
    jpResult: 'none',
    frameType: input.frameType,
    imageUrl: input.imageUrl,
    videoUrl: input.videoUrl,
    gameUrl: input.gameUrl
  });

  // ジャックポット機能は廃止: 抽選は実施せず、確率は常に0・結果は常に none
  const p = 0;
  logger.info('lottery.disabled', { anonId: user.anonId });

  // 即時報酬を実施（抽選結果とは独立）
  const reward = await grantImmediateRewards(user, { boostRarity: !!input.gameUrl });

  // 通知ジョブを投入
  await enqueueNotification({
    anonId: user.anonId,
    message: '提出ありがとうございます！',
    title: reward.title,
    cardId: reward.cardId,
  });

  // ジャックポット結果の反映は廃止

  // ジャックポット記録は廃止
  const jackpotRecordedAt: string | null = null;

  return {
    jpResult: 'none',
    probability: p,
    bonusCount: user.lotteryBonusCount,
    rewardTitle: reward.title,
    rewardCardId: reward.cardId,
    rewardCard: reward.cardMeta ? {
      card_id: reward.cardMeta.card_id,
      card_name: reward.cardMeta.card_name,
      rarity: (reward.cardMeta.rarity as any) || undefined,
      image_url: reward.cardMeta.image_url ?? undefined
    } : undefined,
    jackpotRecordedAt
  };
}
