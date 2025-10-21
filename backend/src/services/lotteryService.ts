import { SubmissionModel } from '../../models/Submission.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import type { UserMeta } from '../../models/UserMeta.js';
import { enqueueNotification } from '../queue/notificationQueue.js';
import { JackpotWinModel } from '../../models/JackpotWin.js';
import { logger } from '../utils/logger.js';
import { loadCardMaster, drawCharacter, toPublicCard } from '../data/cardMaster.js';
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

  // マスターからキャラクターカードを抽選（なければフォールバックID）
  let chosenCardId = `card_${now.getTime()}`;
  let cardMeta: { card_id: string; card_name: string; rarity?: string; image_url?: string | null } | undefined;
  try {
    const master = await loadCardMaster();
    // ゲーム投稿時は SSR/SR のレアリティ抽選確率を +1% ずつ上げる（合計は N から減算）
    let picked = null as any;
    if (opts?.boostRarity) {
      const byRarity = {
        SSR: master.filter(r => r.card_type === 'Character' && r.rarity === 'SSR'),
        SR:  master.filter(r => r.card_type === 'Character' && r.rarity === 'SR'),
        R:   master.filter(r => r.card_type === 'Character' && r.rarity === 'R'),
        N:   master.filter(r => r.card_type === 'Character' && r.rarity === 'N'),
      } as const;
      const base = { SSR: 0.01, SR: 0.04, R: 0.20, N: 0.75 };
      const boost = 0.01;
      const rates = { SSR: base.SSR + boost, SR: base.SR + boost, R: base.R, N: Math.max(0, 1 - (base.SSR + base.SR + base.R + base.N) + base.N - 2*boost) } as any;
      // 上の式がやや分かりづらいので単純化
      rates.N = Math.max(0, 1 - (rates.SSR + rates.SR + rates.R));
      type RKey = 'SSR' | 'SR' | 'R' | 'N';
      const items: [RKey, number][] = [['SSR', rates.SSR], ['SR', rates.SR], ['R', rates.R], ['N', rates.N]];
      const total = items.reduce((s, [, w]) => s + w, 0);
      let r = Math.random() * total;
      let selected: RKey = 'N';
      for (const [k, w] of items) { r -= w; if (r <= 0) { selected = k; break; } }
      const pool = byRarity[selected as RKey];
      picked = pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
      if (!picked) {
        const any = master.filter(r => r.card_type === 'Character');
        picked = any.length ? any[Math.floor(Math.random() * any.length)] : null;
      }
    } else {
      picked = await drawCharacter(master);
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
  jpResult: 'win' | 'lose' | 'none';
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

  // 抽選（当日の初回のみ）
  let p = 0;
  let isWin = false;
  if (!alreadyToday) {
    p = calculateFinalProbability(user.lotteryBonusCount);
    isWin = drawWithProbability(p);
    logger.info('lottery.draw', { anonId: user.anonId, p, isWin });
    if (isWin) {
      user.lotteryBonusCount = 0; // 当選でリセット
    } else {
      user.lotteryBonusCount = (user.lotteryBonusCount || 0) + 1; // 非当選で加算
    }
    await user.save();
  } else {
    logger.info('lottery.skipped.already_submitted_today', { anonId: user.anonId });
  }

  // 即時報酬を実施（抽選結果とは独立）
  const reward = await grantImmediateRewards(user, { boostRarity: !!input.gameUrl });

  // 通知ジョブを投入
  await enqueueNotification({
    anonId: user.anonId,
    message: isWin ? 'ジャックポット当選！' : '提出ありがとうございます！',
    title: reward.title,
    cardId: reward.cardId,
  });

  // 提出に結果を反映（任意）
  // 当日の初回提出のみ抽選結果を反映
  if (!alreadyToday) {
    submission.jpResult = isWin ? 'win' : 'lose';
    await submission.save();
  }

  // 一日一回のみのジャックポット記録（勝利時だけ）
  let jackpotRecordedAt: string | null = null;
  if (!alreadyToday && isWin) {
    const now = new Date();
    const s = startOfJstDay(now);
    const e = endOfJstDay(now);
    const already = await JackpotWinModel.findOne({
      anonId: user.anonId,
      createdAt: { $gte: s, $lte: e }
    }).lean();
    if (!already) {
      const doc = await JackpotWinModel.create({ anonId: user.anonId, displayName: (user as any).displayName || '' });
      jackpotRecordedAt = doc.createdAt.toISOString();
    }
  }

  return {
    jpResult: alreadyToday ? 'none' : (isWin ? 'win' : 'lose'),
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
