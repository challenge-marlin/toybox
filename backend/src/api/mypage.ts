import { Router } from 'express';
import type { Request, Response } from 'express';
import { requireAnonAuth } from '../middleware/auth.js';
import { SubmissionModel } from '../../models/Submission.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import { incFeedServed, incProfileView } from '../utils/metrics.js';
import { startOfJstDay, endOfJstDay } from '../utils/time.js';
import type { FeedResponseDto, SubmissionsResponseDto } from '../dto/FeedItemDto.js';
import type { UserProfileDto } from '../dto/UserDto.js';
import { UserModel } from '../../models/User.js';

export const mypageRouter = Router();

function startOfDay(d: Date): Date { return startOfJstDay(d); }
function endOfDay(d: Date): Date { return endOfJstDay(d); }

function sampleImageUrl(ix: number): string {
  const i = (Math.abs(ix) % 3) + 1;
  return `/uploads/sample_${i}.svg`;
}

// お題（お仕事系）
mypageRouter.get('/topic/work', async (_req: Request, res: Response) => {
  const topics = [
    '業務フローを効率化する自動化',
    '営業資料のテンプレート改善',
    '社内ナレッジの検索性向上',
    '顧客対応の応答品質を上げる仕組み',
    'レポート作成の定型化/可視化'
  ];
  const day = Number(new Date().toISOString().slice(0,10).replace(/-/g,''));
  const idx = day % topics.length;
  res.json({ topic: topics[idx] });
});

// お題（お遊び）
mypageRouter.get('/topic/play', async (_req: Request, res: Response) => {
  const topics = [
    'AIでオリジナルキャラ',
    '一発芸プロンプト',
    '架空商品の広告コピー',
    '変な機械の設計図',
    '空想世界の地図'
  ];
  const day = Number(new Date().toISOString().slice(0,10).replace(/-/g,''));
  const idx = day % topics.length;
  res.json({ topic: topics[idx] });
});

// /topics アーカイブ機能は削除

// 自分の提出（最新 N 件）
mypageRouter.get('/submissions/me', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const limit = Math.min(50, Math.max(1, Number((req.query.limit as string) || 12)));
  
  // aggregationで _id 重複を排除してから sort → limit
  const docs = await SubmissionModel.aggregate([
    { $match: { submitterAnonId: anonId } },
    { $group: { _id: '$_id', doc: { $first: '$$ROOT' } } },
    { $replaceRoot: { newRoot: '$doc' } },
    { $sort: { createdAt: -1 } },
    { $limit: limit }
  ] as any);
  
  // 自分のアバター取得
  const userMeta = await UserMetaModel.findOne({ anonId }, { avatarUrl: 1 }).lean();
  const userAvatar = (userMeta as any)?.avatarUrl ?? null;
  
  // リクエストユーザーの likedSubmissionIds
  let likedSet: Set<string> = new Set();
  try {
    const meMeta = await UserMetaModel.findOne({ anonId }, { likedSubmissionIds: 1 }).lean();
    if (meMeta && Array.isArray((meMeta as any).likedSubmissionIds)) likedSet = new Set<string>((meMeta as any).likedSubmissionIds.map(String));
  } catch {}

  const response: SubmissionsResponseDto = {
    items: docs.map((d: any, i: number) => {
      const submissionImageUrl = d.imageUrl || null;
      const submissionVideoUrl = d.videoUrl || null;
      const displayImageUrl = submissionImageUrl || submissionVideoUrl || userAvatar || sampleImageUrl(i);
      return {
        id: String(d._id),
        createdAt: d.createdAt,
        imageUrl: submissionImageUrl,
        videoUrl: submissionVideoUrl,
        displayImageUrl,
        gameUrl: (d as any).gameUrl || null,
        likesCount: Number((d as any).likesCount || 0),
        liked: likedSet.has(String(d._id))
      };
    })
  };
  res.json(response);
});

// 通知一覧（新しい順）
mypageRouter.get('/notifications', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const limit = Math.min(100, Math.max(1, Number((req.query.limit as string) || 20)));
  const offset = Math.max(0, Number((req.query.offset as string) || 0));
  try {
    const meta = await UserMetaModel.findOne({ anonId }, { notifications: 1 }).lean();
    const all = Array.isArray((meta as any)?.notifications) ? (meta as any).notifications : [];
    const items = all.slice(offset, offset + limit);
    const unread = all.filter((n: any) => !n.read).length;
    return res.json({ items, unread, nextOffset: offset + items.length < all.length ? offset + items.length : null });
  } catch (err) {
    return res.json({ items: [], unread: 0, nextOffset: null });
  }
});

// 通知を既読化
mypageRouter.post('/notifications/read', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const ids: number[] = Array.isArray(req.body?.indexes) ? req.body.indexes.map((x: any) => Number(x)).filter((x: any) => Number.isFinite(x)) : [];
  try {
    if (ids.length === 0) {
      await UserMetaModel.updateOne({ anonId }, { $set: { 'notifications.$[].read': true } });
      return res.json({ ok: true });
    }
    // 指定indexを既読化（位置ベース）
    const meta = await UserMetaModel.findOne({ anonId }, { notifications: 1 }).lean();
    const all = Array.isArray((meta as any)?.notifications) ? (meta as any).notifications : [];
    for (const i of ids) {
      if (i >= 0 && i < all.length) all[i].read = true;
    }
    await UserMetaModel.updateOne({ anonId }, { $set: { notifications: all } });
    return res.json({ ok: true });
  } catch (err) {
    return res.json({ ok: false });
  }
});

// フィード（降順ページング、cursor は ISO 日時）
// imageUrl優先度: submission.imageUrl（投稿画像） → user.avatarUrl
mypageRouter.get('/feed', async (req: Request, res: Response) => {
  const limit = Math.min(50, Math.max(1, Number((req.query.limit as string) || 10)));
  const cursor = req.query.cursor ? new Date(String(req.query.cursor)) : null;
  const q: any = {};
  if (cursor && !isNaN(cursor.getTime())) q.createdAt = { $lt: cursor };
  const docs = await SubmissionModel.find(q).sort({ createdAt: -1 }).limit(limit).lean();

  // まとめて称号（activeTitle）とavatarを取得
  const anonIds = Array.from(new Set((docs as any[]).map((d) => String(d.submitterAnonId))));
  const metas = await UserMetaModel.find({ anonId: { $in: anonIds } }, { anonId: 1, activeTitle: 1, avatarUrl: 1, displayName: 1 }).lean();
  const anonIdToTitle = new Map<string, string | null>();
  const anonIdToAvatar = new Map<string, string | null>();
  const anonIdToName = new Map<string, string | null>();
  for (const m of metas as any[]) {
    anonIdToTitle.set(String(m.anonId), (m as any).activeTitle ?? null);
    anonIdToAvatar.set(String(m.anonId), (m as any).avatarUrl ?? null);
    anonIdToName.set(String(m.anonId), (m as any).displayName ?? null);
  }

  // リクエストユーザーの likedSubmissionIds（存在すれば）
  let likedSet: Set<string> | null = null;
  try {
    let reqUserAnonId: string | undefined = (req as any).anonId;
    if (!reqUserAnonId && (req as any).userId) {
      const u = await UserModel.findById((req as any).userId, { anonId: 1 }).lean();
      reqUserAnonId = (u as any)?.anonId || undefined;
    }
    if (reqUserAnonId) {
      const meMeta = await UserMetaModel.findOne({ anonId: reqUserAnonId }, { likedSubmissionIds: 1 }).lean();
      if (meMeta && Array.isArray((meMeta as any).likedSubmissionIds)) likedSet = new Set<string>((meMeta as any).likedSubmissionIds.map(String));
    }
  } catch {}

  const response: FeedResponseDto = {
    items: docs.map((d) => {
      const submissionImageUrl = (d as any).imageUrl || null;
      const submissionVideoUrl = (d as any).videoUrl || null;
      const submissionGameUrl = (d as any).gameUrl || null;
      const userAvatar = anonIdToAvatar.get(String((d as any).submitterAnonId)) ?? null;
      const displayImageUrl = submissionImageUrl || submissionVideoUrl || userAvatar;
      return {
        id: String(d._id),
        anonId: (d as any).submitterAnonId,
        displayName: anonIdToName.get(String((d as any).submitterAnonId)) ?? null,
        createdAt: (d as any).createdAt,
        imageUrl: submissionImageUrl,
        videoUrl: submissionVideoUrl,
        avatarUrl: userAvatar,
        displayImageUrl,
        title: anonIdToTitle.get(String((d as any).submitterAnonId)) ?? null,
        gameUrl: submissionGameUrl,
        likesCount: Number((d as any).likesCount || 0),
        liked: likedSet ? likedSet.has(String((d as any)._id)) : false
      };
    }),
    nextCursor: docs.length > 0 ? (docs[docs.length - 1] as any).createdAt : null
  };
  
  res.json(response);
  try { incFeedServed(); } catch {}
});

// 当日の提出者一覧（ユニーク anonId）
mypageRouter.get('/submitters/today', async (_req: Request, res: Response) => {
  const s = startOfDay(new Date());
  const e = endOfDay(new Date());
  const docs = await SubmissionModel.find({ createdAt: { $gte: s, $lte: e } }, { submitterAnonId: 1 })
    .lean();
  const set = new Set<string>(docs.map((d: any) => d.submitterAnonId));
  // 併せて displayName を返す
  const ids = Array.from(set);
  const metas = await UserMetaModel.find({ anonId: { $in: ids } }, { anonId: 1, displayName: 1 }).lean();
  const nameMap = new Map<string, string | null>();
  for (const m of metas as any[]) {
    nameMap.set(String(m.anonId), (m as any).displayName ?? null);
  }
  res.json({ submitters: ids.map((id) => ({ anonId: id, displayName: nameMap.get(id) ?? null })) });
});

// デイリーランキング（暫定: 件数順）
mypageRouter.get('/ranking/daily', async (req: Request, res: Response) => {
  const dateStr = (req.query.date as string) || new Date().toISOString().slice(0,10);
  const day = new Date(dateStr);
  const s = startOfDay(day);
  const e = endOfDay(day);
  const agg = await SubmissionModel.aggregate([
    { $match: { createdAt: { $gte: s, $lte: e } } },
    { $group: { _id: '$submitterAnonId', count: { $sum: 1 } } },
    { $sort: { count: -1 } },
    { $limit: 10 }
  ] as any);
  // 併せて displayName を返す
  const ids = agg.map((x: any) => String(x._id));
  const metas = await UserMetaModel.find({ anonId: { $in: ids } }, { anonId: 1, displayName: 1 }).lean();
  const nameMap = new Map<string, string | null>();
  for (const m of metas as any[]) {
    nameMap.set(String(m.anonId), (m as any).displayName ?? null);
  }
  res.json({ ranking: agg.map((x: any) => ({ anonId: x._id, count: x.count, displayName: nameMap.get(String(x._id)) ?? null })) });
});

// 公開プロフィール
mypageRouter.get('/user/profile/:anonId', async (req: Request, res: Response) => {
  const anonId = String(req.params.anonId);
  const user = await UserMetaModel.findOne({ anonId }).lean();
  
  // 称号の有効期限チェック
  let activeTitle = (user as any)?.activeTitle ?? null;
  let activeTitleUntil = (user as any)?.activeTitleUntil ?? null;
  
  if (activeTitle && activeTitleUntil) {
    const now = new Date();
    const until = new Date(activeTitleUntil);
    if (until <= now) {
      activeTitle = null;
      activeTitleUntil = null;
    }
  }
  
  const payload: UserProfileDto = user ? {
    anonId,
    activeTitle,
    activeTitleUntil,
    displayName: (user as any).displayName ?? '',
    avatarUrl: (user as any).avatarUrl ?? null,
    headerUrl: (user as any).headerUrl ?? null,
    bio: (user as any).bio ?? '',
    cardsAlbum: Array.isArray((user as any).cardsAlbum) ? (user as any).cardsAlbum : [],
    updatedAt: (user as any).updatedAt ?? null
  } : {
    anonId,
    activeTitle: null,
    activeTitleUntil: null,
    displayName: '',
    avatarUrl: null,
    headerUrl: null,
    bio: '',
    cardsAlbum: [],
    updatedAt: null
  };
  res.json(payload);
  try { incProfileView(); } catch {}
});

// 指定ユーザーの提出一覧
mypageRouter.get('/user/submissions/:anonId', async (req: Request, res: Response) => {
  const anonId = String(req.params.anonId);
  const limit = Math.min(50, Math.max(1, Number((req.query.limit as string) || 12)));
  const cursor = req.query.cursor ? new Date(String(req.query.cursor)) : null;
  const q: any = { submitterAnonId: anonId };
  if (cursor && !isNaN(cursor.getTime())) q.createdAt = { $lt: cursor };
  const docs = await SubmissionModel.find(q).sort({ createdAt: -1 }).limit(limit).lean();
  
  // ユーザーのアバター取得
  const userMeta = await UserMetaModel.findOne({ anonId }, { avatarUrl: 1 }).lean();
  const userAvatar = (userMeta as any)?.avatarUrl ?? null;

  // リクエストユーザーの likedSubmissionIds（存在すれば）
  let likedSet: Set<string> | null = null;
  try {
    let reqUserAnonId: string | undefined = (req as any).anonId;
    if (!reqUserAnonId && (req as any).userId) {
      const u = await UserModel.findById((req as any).userId, { anonId: 1 }).lean();
      reqUserAnonId = (u as any)?.anonId || undefined;
    }
    if (reqUserAnonId) {
      const meMeta = await UserMetaModel.findOne({ anonId: reqUserAnonId }, { likedSubmissionIds: 1 }).lean();
      if (meMeta && Array.isArray((meMeta as any).likedSubmissionIds)) likedSet = new Set<string>((meMeta as any).likedSubmissionIds.map(String));
    }
  } catch {}
  
  const response: SubmissionsResponseDto = {
    items: docs.map((d, i) => {
      const submissionImageUrl = (d as any).imageUrl || null;
      const submissionVideoUrl = (d as any).videoUrl || null;
      const submissionGameUrl = (d as any).gameUrl || null;
      const displayImageUrl = submissionImageUrl || submissionVideoUrl || userAvatar || sampleImageUrl(i);
      return {
        id: String(d._id),
        createdAt: (d as any).createdAt,
        imageUrl: submissionImageUrl,
        videoUrl: submissionVideoUrl,
        displayImageUrl,
        gameUrl: submissionGameUrl,
        likesCount: Number((d as any).likesCount || 0),
        liked: likedSet ? likedSet.has(String((d as any)._id)) : false
      };
    }),
    nextCursor: docs.length > 0 ? (docs[docs.length - 1] as any).createdAt : null
  };
  res.json(response);
});

// 自分の提出を削除（所有者のみ）
mypageRouter.delete('/submissions/:id', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const id = String(req.params.id);
  try {
    const doc = await SubmissionModel.findOne({ _id: id, submitterAnonId: anonId }).lean();
    if (!doc) return res.status(404).json({ error: 'Not Found' });
    await SubmissionModel.deleteOne({ _id: id });
    return res.json({ ok: true });
  } catch (err) {
    throw err;
  }
});

// いいね（追加）
mypageRouter.post('/submissions/:id/like', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const id = String(req.params.id);
  try {
    const sub = await SubmissionModel.findById(id).lean();
    if (!sub) return res.status(404).json({ error: 'Not Found' });

    const r = await UserMetaModel.updateOne(
      { anonId },
      { $addToSet: { likedSubmissionIds: id } },
      { upsert: true }
    );
    if ((r as any).modifiedCount > 0 || (r as any).upsertedCount > 0) {
      await SubmissionModel.updateOne({ _id: id }, { $inc: { likesCount: 1 } });
      // 通知作成（自分で自分にいいねは通知しない）
      try {
        const targetAnon = String((sub as any).submitterAnonId);
        if (targetAnon && targetAnon !== anonId) {
          const likerMeta = await UserMetaModel.findOne({ anonId }, { displayName: 1 }).lean();
          const likerName = ((likerMeta as any)?.displayName || anonId) as string;
          const msg = `${likerName} さんからいいねがつきました`;
          await UserMetaModel.updateOne(
            { anonId: targetAnon },
            { $push: { notifications: { $each: [{ type: 'like', fromAnonId: anonId, submissionId: id, message: msg, createdAt: new Date(), read: false }], $position: 0 } } },
            { upsert: true }
          );
        }
      } catch {}
    }
    const doc = await SubmissionModel.findById(id, { likesCount: 1 }).lean();
    return res.json({ ok: true, likesCount: Number((doc as any)?.likesCount || 0), liked: true });
  } catch (err) {
    throw err;
  }
});

// いいね（削除）
mypageRouter.delete('/submissions/:id/like', requireAnonAuth, async (req: Request, res: Response) => {
  const anonId = (req as any).anonId as string;
  const id = String(req.params.id);
  try {
    const sub = await SubmissionModel.findById(id).lean();
    if (!sub) return res.status(404).json({ error: 'Not Found' });

    const r = await UserMetaModel.updateOne(
      { anonId },
      { $pull: { likedSubmissionIds: id } }
    );
    if ((r as any).modifiedCount > 0) {
      await SubmissionModel.updateOne({ _id: id, likesCount: { $gt: 0 } }, { $inc: { likesCount: -1 } });
    }
    const doc = await SubmissionModel.findById(id, { likesCount: 1 }).lean();
    return res.json({ ok: true, likesCount: Number((doc as any)?.likesCount || 0), liked: false });
  } catch (err) {
    throw err;
  }
});


