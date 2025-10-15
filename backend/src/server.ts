import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';
import { submitRouter } from './api/submit.js';
import { userRouter } from './api/user.js';
import { authRouter } from './api/auth.js';
import { requireAnonAuth } from './middleware/auth.js';
import { optionalAuth } from './middleware/requireAuth.js';
import { requestLogger, responseTimeLogger } from './middleware/logging.js';
import { centralErrorHandler } from './middleware/errorHandler.js';
import { metricsText, incRequest, incError } from './utils/metrics.js';
import { rateLimitByAnonOrIp } from './middleware/rateLimit.js';
import { mypageRouter } from './api/mypage.js';
import { cardsRouter } from './api/cards.js';
import path from 'path';

dotenv.config();

const app = express();

const allowlist = (process.env.CORS_ORIGINS || 'http://localhost:3000')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

app.use(
  cors({
    origin(origin, callback) {
      if (!origin) return callback(null, true);
      if (allowlist.includes(origin)) return callback(null, true);
      return callback(new Error('Not allowed by CORS'));
    },
    credentials: true
  })
);

app.use(express.json());
app.use(cookieParser());
app.use(requestLogger);
app.use((req, _res, next) => { incRequest(); next(); });
app.use(responseTimeLogger);

const mongoUri = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/toybox';
const port = Number(process.env.PORT || 4000);
let mongoReady = false;

async function start() {
  try {
    await mongoose.connect(mongoUri, {
      dbName: process.env.MONGODB_DB || 'toybox'
    } as any);
    mongoReady = true;
    console.log('[server] Connected to MongoDB');

    // 起動時に User コレクションのインデックスを再作成（部分ユニーク化）
    try {
      const { UserModel } = await import('../models/User.js');
      // 既存の email / username インデックスを確認して削除（存在すれば）
      try { await (UserModel as any).collection.dropIndex('email_1'); } catch {}
      try { await (UserModel as any).collection.dropIndex('username_1'); } catch {}
      // Mongoose の ensureIndexes を再実行（schemaで定義した partialFilterExpression を適用）
      await UserModel.syncIndexes();
      console.log('[server] User indexes synchronized');
    } catch (e) {
      console.warn('[server] Failed to sync User indexes:', e instanceof Error ? e.message : String(e));
    }

    app.get('/health', (_req: express.Request, res: express.Response) => {
      res.json({ status: 'ok' });
    });

    app.get('/ready', (_req: express.Request, res: express.Response) => {
      if (mongoReady) return res.json({ ready: true });
      return res.status(503).json({ ready: false });
    });

    app.get('/metrics', (_req: express.Request, res: express.Response) => {
      res.setHeader('Content-Type', 'text/plain; version=0.0.4');
      res.send(metricsText());
    });

    // Root route: simple info for convenience
    app.get('/', (_req: express.Request, res: express.Response) => {
      res.json({
        name: 'ToyBox API',
        status: 'running',
        see: ['/health', '/ready', '/metrics', '/api/topic/today']
      });
    });

    // レート制限（書き込み系のみに適用）: 1分に 120 リクエスト（anonId or IP）
    const writeRateLimit = rateLimitByAnonOrIp({ windowMs: 60_000, max: 120 });
    app.use('/api', (req, res, next) => {
      const m = req.method;
      if (m === 'GET' || m === 'OPTIONS' || m === 'HEAD') return next();
      return writeRateLimit(req, res, next);
    });

    // 認証API（公開）
    app.use('/api', authRouter);

    // 公開/一部認証 API（マイページ）を先に適用（feed 等は認証不要）
    // optionalAuth により JWT から anonId を解決できるようにする
    app.use('/api', optionalAuth, mypageRouter);

    // 画像などの静的ファイル提供（/uploads を公開）
    // Cache-Control を短く設定（1時間）してキャッシュを制御
    app.use('/uploads', (req, res, next) => {
      res.setHeader('Cache-Control', 'public, max-age=3600');
      next();
    }, express.static(path.resolve(process.cwd(), 'public', 'uploads')));

    // 認証が必要な API は後段に適用
    app.use('/api', requireAnonAuth, submitRouter);
    app.use('/api', requireAnonAuth, userRouter);
    app.use('/api', requireAnonAuth, cardsRouter);

    app.use(centralErrorHandler);

    app.listen(port, () => {
      console.log(`[server] Listening on http://localhost:${port}`);
    });
  } catch (err) {
    console.error('[server] Failed to start:', err);
    process.exit(1);
  }
}

start();
