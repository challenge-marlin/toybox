import { Router } from 'express';
import { handleSubmissionAndLottery } from '../services/lotteryService.js';
import { requireString, requireStringArrayLen, pickValidationErrors } from '../utils/validation.js';
import { logger } from '../utils/logger.js';
import type { SubmissionResultDto } from '../dto/SubmissionDto.js';
import { uploadPost, uploadGameZip } from '../lib/upload.js';
import { v2 as cloudinary } from 'cloudinary';
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

    cloudinary.config({
      cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
      api_key: process.env.CLOUDINARY_API_KEY,
      api_secret: process.env.CLOUDINARY_API_SECRET
    });

    const folder = `toybox/submissions/${anonId}`;
    const resourceType = (req.file.mimetype || '').startsWith('video/') ? 'video' : 'image';
    const result: any = await new Promise((resolve, reject) => {
      const stream = cloudinary.uploader.upload_stream(
        { folder, resource_type: resourceType },
        (error, result) => {
          if (error) return reject(error);
          resolve(result);
        }
      );
      stream.end(req.file.buffer);
    });

    const response = resourceType === 'video'
      ? { ok: true, public_id: result.public_id, secure_url: result.secure_url, videoUrl: result.secure_url }
      : { ok: true, public_id: result.public_id, secure_url: result.secure_url, imageUrl: result.secure_url };

    logger.info('submit.upload.success', { anonId, public_id: result.public_id, url: result.secure_url, type: resourceType });
    return res.json(response);
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
