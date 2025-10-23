import { Router } from 'express';
import { UserMetaModel } from '../../models/UserMeta.js';
import { logger } from '../utils/logger.js';
import { uploadAvatar, uploadHeader } from '../lib/upload.js';
import { UpdateBioSchema, UpdateDisplayNameSchema } from '../validation/user.js';
import { UnauthorizedError, BadRequestError } from '../middleware/errorHandler.js';
import type { UserMeDto, UpdateProfileResponse } from '../dto/UserDto.js';

export const userRouter = Router();

userRouter.get('/user/me', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!anonId) throw new UnauthorizedError();

    const user = await UserMetaModel.findOne({ anonId });
    
    // 称号の有効期限チェック（JST基準）
    let activeTitle = user?.activeTitle || null;
    let activeTitleUntil = user?.activeTitleUntil || null;
    
    if (activeTitle && activeTitleUntil) {
      const now = new Date();
      const until = new Date(activeTitleUntil);
      // 有効期限が過ぎている場合は称号をクリア
      if (until <= now) {
        activeTitle = null;
        activeTitleUntil = null;
        // DBからも削除（オプション）
        if (user) {
          user.activeTitle = undefined;
          user.activeTitleUntil = undefined;
          await user.save();
        }
      }
    }
    
    const payload: UserMeDto = user ? {
      anonId: user.anonId,
      activeTitle,
      activeTitleUntil,
      cardsAlbum: user.cardsAlbum || [],
      lotteryBonusCount: user.lotteryBonusCount || 0
    } : {
      anonId,
      activeTitle: null,
      activeTitleUntil: null,
      cardsAlbum: [],
      lotteryBonusCount: 0
    };

    logger.info('user.me', { anonId });
    return res.json(payload);
  } catch (err) {
    next(err);
  }
});

// プロフィール更新（自己紹介）
userRouter.post('/user/profile/bio', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    const parsed = UpdateBioSchema.parse(req.body);
    const bio = parsed.bio.slice(0, 1000);
    
    const user = await UserMetaModel.findOneAndUpdate(
      { anonId },
      { $set: { bio } },
      { new: true, upsert: true }
    ).lean();
    
    const response: UpdateProfileResponse = { ok: true, bio: (user as any)?.bio || '' };
    logger.info('user.profile.bio.updated', { anonId });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});

// プロフィール更新（表示名）
userRouter.post('/user/profile/name', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    const parsed = UpdateDisplayNameSchema.parse(req.body);
    const displayName = parsed.displayName.trim().slice(0, 50);
    
    const user = await UserMetaModel.findOneAndUpdate(
      { anonId },
      { $set: { displayName } },
      { new: true, upsert: true }
    ).lean();
    
    const response: UpdateProfileResponse = { ok: true, displayName: (user as any)?.displayName || '' };
    logger.info('user.profile.name.updated', { anonId });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});

// 画像アップロード（avatar）
userRouter.post('/user/profile/avatar', uploadAvatar.single('file'), async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!req.file) throw new BadRequestError('No file uploaded');
    
    const relUrl = `/uploads/${req.file.filename}`;
    await UserMetaModel.findOneAndUpdate(
      { anonId },
      { $set: { avatarUrl: relUrl } },
      { upsert: true }
    );
    
    const response: UpdateProfileResponse = { ok: true, avatarUrl: relUrl };
    logger.info('user.profile.avatar.uploaded', { anonId, path: relUrl });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});

// 画像アップロード（header）
userRouter.post('/user/profile/header', uploadHeader.single('file'), async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!req.file) throw new BadRequestError('No file uploaded');
    
    const relUrl = `/uploads/${req.file.filename}`;
    await UserMetaModel.findOneAndUpdate(
      { anonId },
      { $set: { headerUrl: relUrl } },
      { upsert: true }
    );
    
    const response: UpdateProfileResponse = { ok: true, headerUrl: relUrl };
    logger.info('user.profile.header.uploaded', { anonId, path: relUrl });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});

// 統合アップロードエンドポイント（type=avatar|header）
userRouter.post('/user/profile/upload', async (req, res, next) => {
  // 互換のため kind も受理
  const typeParam = (req.query.type as string) || (req.body?.type as string) || (req.query.kind as string) || (req.body?.kind as string);
  const type = typeParam as 'avatar' | 'header' | undefined;
  
  if (!type || !['avatar', 'header'].includes(type)) {
    return next(new BadRequestError('Invalid or missing type parameter (avatar|header)'));
  }

  const middleware = type === 'avatar' ? uploadAvatar : uploadHeader;
  
  middleware.single('file')(req, res, async (err) => {
    if (err) return next(err);
    
    try {
      const anonId = (req as any).anonId as string;
      if (!req.file) throw new BadRequestError('No file uploaded');
      
      const relUrl = `/uploads/${req.file.filename}`;
      const updateField = type === 'avatar' ? { avatarUrl: relUrl } : { headerUrl: relUrl };
      
      await UserMetaModel.findOneAndUpdate(
        { anonId },
        { $set: updateField },
        { upsert: true }
      );
      
      const response: UpdateProfileResponse = { ok: true, ...updateField };
      logger.info('user.profile.upload', { anonId, type, path: relUrl });
      return res.json(response);
    } catch (err) {
      next(err);
    }
  });
});

// プロフィール一括更新（PATCH）
userRouter.patch('/user/profile', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    const updates: any = {};
    
    // displayNameのバリデーション
    if (req.body.displayName !== undefined) {
      const parsed = UpdateDisplayNameSchema.parse({ displayName: req.body.displayName });
      updates.displayName = parsed.displayName.trim().slice(0, 50);
    }
    
    // bioのバリデーション
    if (req.body.bio !== undefined) {
      const parsed = UpdateBioSchema.parse({ bio: req.body.bio });
      updates.bio = parsed.bio.slice(0, 1000);
    }
    
    // avatarUrlのバリデーション（文字列かつ妥当なURL形式）
    if (req.body.avatarUrl !== undefined) {
      const url = String(req.body.avatarUrl).trim();
      if (url && (url.startsWith('/uploads/') || url.startsWith('http://') || url.startsWith('https://'))) {
        updates.avatarUrl = url.slice(0, 500);
      } else if (!url) {
        updates.avatarUrl = null;
      } else {
        throw new BadRequestError('Invalid avatarUrl format');
      }
    }
    
    // headerUrlのバリデーション
    if (req.body.headerUrl !== undefined) {
      const url = String(req.body.headerUrl).trim();
      if (url && (url.startsWith('/uploads/') || url.startsWith('http://') || url.startsWith('https://'))) {
        updates.headerUrl = url.slice(0, 500);
      } else if (!url) {
        updates.headerUrl = null;
      } else {
        throw new BadRequestError('Invalid headerUrl format');
      }
    }
    
    if (Object.keys(updates).length === 0) {
      throw new BadRequestError('No valid fields to update');
    }
    
    const user = await UserMetaModel.findOneAndUpdate(
      { anonId },
      { $set: updates },
      { new: true, upsert: true }
    ).lean();
    
    const response: UserMeDto = {
      anonId: user.anonId,
      activeTitle: user.activeTitle || null,
      activeTitleUntil: user.activeTitleUntil || null,
      cardsAlbum: user.cardsAlbum || [],
      lotteryBonusCount: user.lotteryBonusCount || 0
    };
    
    logger.info('user.profile.patched', { anonId, updates: Object.keys(updates) });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});
