import { Router } from 'express';
import { handleSubmissionAndLottery } from '../services/lotteryService.js';
import { requireString, requireStringArrayLen, pickValidationErrors } from '../utils/validation.js';
import { logger } from '../utils/logger.js';
import type { SubmissionResultDto } from '../dto/SubmissionDto.js';
import { uploadPost } from '../lib/upload.js';
import { SubmissionModel } from '../../models/Submission.js';
import { BadRequestError } from '../middleware/errorHandler.js';

export const submitRouter = Router();

// 画像アップロード（提出は別リクエストで行う）
submitRouter.post('/submit/upload', uploadPost.single('file'), async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!req.file) throw new BadRequestError('No file uploaded');

    const imageUrl = `/uploads/${req.file.filename}`;

    logger.info('submit.upload.success', { anonId, imageUrl });
    // ここでは画像URLのみ返却し、/api/submit で提出・報酬処理を行う
    return res.json({ ok: true, imageUrl });
  } catch (err) {
    next(err);
  }
});

// 既存の提出API（テキストベース）
submitRouter.post('/submit', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    const { aim, steps, frameType, imageUrl } = req.body || {};

    try {
      requireString(aim, 'aim', { max: 100 });
      requireStringArrayLen(steps, 'steps', 3);
      requireString(frameType, 'frameType');
    } catch (ve) {
      const errors = pickValidationErrors(ve);
      return res.status(400).json({ error: 'Bad Request', details: errors });
    }

    const result = await handleSubmissionAndLottery({
      submitterAnonId: anonId,
      aim,
      steps,
      frameType,
      imageUrl
    });

    const response: SubmissionResultDto = {
      jpResult: result.jpResult,
      probability: result.probability,
      bonusCount: result.bonusCount,
      rewardTitle: result.rewardTitle,
      rewardCardId: result.rewardCardId,
      rewardCard: result as any && (result as any).rewardCard ? (result as any).rewardCard : undefined,
      jackpotRecordedAt: result.jackpotRecordedAt
    };

    logger.info('submit.success', { anonId, jpResult: result.jpResult, p: result.probability, bonus: result.bonusCount });
    return res.json(response);
  } catch (err) {
    next(err);
  }
});
