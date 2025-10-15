import { SubmissionModel } from '../../models/Submission.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import type { UserMeta } from '../../models/UserMeta.js';
import { enqueueNotification } from '../queue/notificationQueue.js';
import { JackpotWinModel } from '../../models/JackpotWin.js';
import { logger } from '../utils/logger.js';
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
export async function grantImmediateRewards(user: UserMeta): Promise<{ user: UserMeta; title: string; cardId: string }> {
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

  const newCardId = `card_${now.getTime()}`;

  user.activeTitle = chosen;
  user.activeTitleUntil = until;
  user.cardsAlbum = [...(user.cardsAlbum || []), { id: newCardId, obtainedAt: now }];

  await user.save();
  logger.info('reward.granted', { anonId: user.anonId, title: chosen, cardId: newCardId });
  return { user, title: chosen, cardId: newCardId };
}

// 提出後の全処理
export interface SubmissionInput {
  submitterAnonId: string;
  aim: string;
  steps: string[];
  frameType: string;
  imageUrl?: string; // 画像アップロード後の相対URL（/uploads/...）
}

export interface SubmissionResult {
  jpResult: 'win' | 'lose' | 'none';
  probability: number;
  bonusCount: number; // 更新後の lotteryBonusCount
  rewardTitle?: string;
  rewardCardId?: string;
  jackpotRecordedAt?: string | null;
}

export async function handleSubmissionAndLottery(input: SubmissionInput): Promise<SubmissionResult> {
  const { submitterAnonId } = input;

  // 1日1回提出制限
  if (await hasSubmittedToday(submitterAnonId)) {
    logger.info('submit.limited', { anonId: submitterAnonId });
    return { jpResult: 'none', probability: 0, bonusCount: 0 };
  }

  // 同時多発（短時間の二重送信）対策: 直近10秒以内に同一内容の提出が存在する場合はスキップ
  // 画像提出は imageUrl が一致、テキスト提出は aim/steps/frameType が一致するものを重複とみなす
  try {
    const tenSecondsAgo = new Date(Date.now() - 10_000);
    const dup = await SubmissionModel.findOne({
      submitterAnonId,
      createdAt: { $gte: tenSecondsAgo },
      ...(input.imageUrl ? { imageUrl: input.imageUrl } : { aim: input.aim, steps: input.steps, frameType: input.frameType })
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
    imageUrl: input.imageUrl
  });

  // 抽選確率
  const p = calculateFinalProbability(user.lotteryBonusCount);
  const isWin = drawWithProbability(p);
  logger.info('lottery.draw', { anonId: user.anonId, p, isWin });

  if (isWin) {
    user.lotteryBonusCount = 0; // 当選でリセット
  } else {
    user.lotteryBonusCount = (user.lotteryBonusCount || 0) + 1; // 非当選で加算
  }
  await user.save();

  // 即時報酬を実施（抽選結果とは独立）
  const reward = await grantImmediateRewards(user);

  // 通知ジョブを投入
  await enqueueNotification({
    anonId: user.anonId,
    message: isWin ? 'ジャックポット当選！' : '提出ありがとうございます！',
    title: reward.title,
    cardId: reward.cardId,
  });

  // 提出に結果を反映（任意）
  submission.jpResult = isWin ? 'win' : 'lose';
  await submission.save();

  // 一日一回のみのジャックポット記録（勝利時だけ）
  let jackpotRecordedAt: string | null = null;
  if (isWin) {
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
    jpResult: isWin ? 'win' : 'lose',
    probability: p,
    bonusCount: user.lotteryBonusCount,
    rewardTitle: reward.title,
    rewardCardId: reward.cardId,
    jackpotRecordedAt
  };
}
