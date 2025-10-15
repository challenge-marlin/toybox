import { Router } from 'express';
import { UserMetaModel } from '../../models/UserMeta.js';
import type { UserMeta } from '../../models/UserMeta.js';
import { BadRequestError, UnauthorizedError } from '../middleware/errorHandler.js';
import { drawCharacter, drawEffect, loadCardMaster, toPublicCard } from '../data/cardMaster.js';

export const cardsRouter = Router();

// POST /api/cards/generate  (alias: /api/v1/toybox/generate_card)
cardsRouter.post(['/cards/generate', '/v1/toybox/generate_card'], async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!anonId) throw new UnauthorizedError();

    const type = ((req.body?.type as string) || 'Character') as 'Character' | 'Effect';
    const master = await loadCardMaster();
    const picked = type === 'Character' ? await drawCharacter(master) : await drawEffect(master);
    if (!picked) throw new BadRequestError('Card pool unavailable');

    const now = new Date();
    const user: UserMeta = (await UserMetaModel.findOne({ anonId })) ||
      (await UserMetaModel.create({ anonId, lotteryBonusCount: 0, cardsAlbum: [] }));

    user.cardsAlbum.push({ id: picked.card_id, obtainedAt: now });
    await user.save();

    const card = toPublicCard(picked);
    return res.json({
      ok: true,
      card,
      obtainedAt: now.toISOString(),
      albumCount: user.cardsAlbum.length
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/cards/me  -> user's album (with joined metadata)
cardsRouter.get('/cards/me', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!anonId) throw new UnauthorizedError();

    const user = await UserMetaModel.findOne({ anonId }).lean();
    const album = user?.cardsAlbum ?? [];

    const master = await loadCardMaster();
    const index = new Map(master.map(r => [r.card_id, r]));
    const entries = album.map(e => {
      const row = index.get(e.id);
      return {
        id: e.id,
        obtainedAt: e.obtainedAt ? new Date(e.obtainedAt).toISOString() : null,
        meta: row ? toPublicCard(row) : null
      };
    });

    return res.json({ ok: true, entries });
  } catch (err) {
    next(err);
  }
});

// GET /api/cards/summary  -> counts and attribute breakdown
cardsRouter.get('/cards/summary', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!anonId) throw new UnauthorizedError();

    const user = await UserMetaModel.findOne({ anonId }).lean();
    const album = user?.cardsAlbum ?? [];
    const master = await loadCardMaster();
    const index = new Map(master.map(r => [r.card_id, r]));

    let total = album.length;
    let ssr = 0, sr = 0, r = 0, n = 0;
    const byAttr: Record<string, number> = { '木': 0, '火': 0, '土': 0, '金': 0, '水': 0 };

    for (const e of album) {
      const row = index.get(e.id);
      if (!row) continue;
      if (row.rarity === 'SSR') ssr++;
      else if (row.rarity === 'SR') sr++;
      else if (row.rarity === 'R') r++;
      else if (row.rarity === 'N') n++;
      if (row.attribute && byAttr[row.attribute] !== undefined) byAttr[row.attribute]++;
    }

    return res.json({ ok: true, total, rarity: { SSR: ssr, SR: sr, R: r, N: n }, byAttr });
  } catch (err) {
    next(err);
  }
});


