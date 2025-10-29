import { Router } from 'express';
import { handleSubmissionAndLottery } from '../services/lotteryService.js';
import { requireString, requireStringArrayLen, pickValidationErrors } from '../utils/validation.js';
import { logger } from '../utils/logger.js';
import type { SubmissionResultDto } from '../dto/SubmissionDto.js';
import { uploadPost, uploadGameZip } from '../lib/upload.js';
import { generateOptimizedImages } from '../lib/upload.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import AdmZip from 'adm-zip';
import { SubmissionModel } from '../../models/Submission.js';
import { BadRequestError } from '../middleware/errorHandler.js';

export const submitRouter = Router();

// 画像/動画アップロード（提出は別リクエストで行う）
submitRouter.post('/submit/upload', uploadPost.single('file'), async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!req.file) throw new BadRequestError('No file uploaded');
    const mime = req.file.mimetype || '';
    const isVideo = mime.startsWith('video/');
    const url = `/uploads/${req.file.filename}`;
    let displayImageUrl: string | undefined;
    if (!isVideo) {
      try {
        const { displayRel } = await generateOptimizedImages(req.file.path, url);
        if (displayRel) displayImageUrl = displayRel;
      } catch {}
    }

    logger.info('submit.upload.success', { anonId, url, type: isVideo ? 'video' : 'image' });
    // ここではURLのみ返却し、/api/submit で提出・報酬処理を行う
    return res.json(isVideo ? { ok: true, videoUrl: url } : { ok: true, imageUrl: url, displayImageUrl });
  } catch (err) {
    next(err);
  }
});

// ゲームZIPアップロード → /uploads/games/{anonId}/{ts}/ に展開し、index.html のURLを返す
submitRouter.post('/submit/uploadGame', uploadGameZip.single('file'), async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    if (!req.file) throw new BadRequestError('No file uploaded');
    if (!req.file.originalname.toLowerCase().endsWith('.zip')) throw new BadRequestError('ZIP file required');

    const baseDir = path.join(process.cwd(), 'public', 'uploads', 'games', anonId);
    const ts = Date.now();
    const destDir = path.join(baseDir, String(ts));
    await fs.mkdir(destDir, { recursive: true });

    const zipPath = path.join(destDir, req.file.filename);
    await fs.writeFile(zipPath, await fs.readFile(req.file.path));

    const zip = new AdmZip(zipPath);
    zip.extractAllTo(destDir, true);
    try { await fs.unlink(zipPath); } catch {}

    // index.html を探す（直下優先、なければ最初の index.html）
    let rel = '' as string | null;
    const walk = async (dir: string): Promise<string | null> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const e of entries) {
        const p = path.join(dir, e.name);
        if (e.isFile() && e.name.toLowerCase() === 'index.html') return p;
      }
      for (const e of entries) {
        if (e.isDirectory()) {
          const r = await walk(path.join(dir, e.name));
          if (r) return r;
        }
      }
      return null;
    };
    const found = await walk(destDir);
    if (!found) throw new BadRequestError('index.html not found in ZIP');
    rel = found.replace(path.join(process.cwd(), 'public'), '').replace(/\\/g, '/');

    const gameUrl = rel;
    return res.json({ ok: true, gameUrl });
  } catch (err) {
    next(err);
  }
});

// 既存の提出API（テキストベース）
submitRouter.post('/submit', async (req, res, next) => {
  try {
    const anonId = (req as any).anonId as string;
    const { aim, steps, frameType, imageUrl, videoUrl, gameUrl } = req.body || {};

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
      imageUrl,
      videoUrl,
      gameUrl
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
