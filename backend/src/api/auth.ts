import { Router } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { UserModel } from '../../models/User.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import { BadRequestError, UnauthorizedError } from '../middleware/errorHandler.js';
import { logger } from '../utils/logger.js';

export const authRouter = Router();

const JWT_SECRET = process.env.JWT_SECRET || 'change_me_strong_secret';
const BCRYPT_ROUNDS = 12;

// バリデーションスキーマ
const RegisterSchema = z.object({
  email: z.string().email().optional(),
  // username は任意（未指定時はサーバ側で自動採番）
  username: z.string().min(3).max(30).regex(/^[a-z0-9_]+$/i).optional(),
  password: z.string().min(8).max(128),
  displayName: z.string().min(1).max(50).optional()
});

const LoginSchema = z.object({
  email: z.string().email().optional(),
  username: z.string().min(3).max(30).regex(/^[a-z0-9_]+$/i).optional(),
  password: z.string()
}).refine((data) => !!data.email || !!data.username, {
  message: 'email or username is required'
});

// 登録
authRouter.post('/auth/register', async (req, res, next) => {
  try {
    const parsed = RegisterSchema.parse(req.body);
    const email = parsed.email?.toLowerCase();
    const rawUsername = parsed.username?.toLowerCase();

    // 既存ユーザーチェック
    if (email) {
      const existingEmail = await UserModel.findOne({ email });
      if (existingEmail) throw new BadRequestError('Email already registered');
    }
    if (rawUsername) {
      const existingUsername = await UserModel.findOne({ username: rawUsername });
      if (existingUsername) throw new BadRequestError('Username already taken');
    }

    // パスワードハッシュ
    const hashedPassword = await bcrypt.hash(parsed.password, BCRYPT_ROUNDS);

    // username 未指定時は自動生成（重複回避）
    let username = rawUsername;
    if (!username) {
      const base = `user${Math.random().toString(36).slice(2, 8)}`;
      let candidate = base;
      for (let tries = 0; tries < 5; tries++) {
        const exists = await UserModel.findOne({ username: candidate });
        if (!exists) { username = candidate; break; }
        candidate = `${base}${Math.random().toString(36).slice(2, 4)}`;
      }
      if (!username) username = `user${Date.now()}`;
    }

    // anonId は username と同一にする
    const anonId = username;
    // displayName が未指定の場合は username を既定値にする
    const displayName = (parsed.displayName && parsed.displayName.trim()) ? parsed.displayName.trim() : username;

    // Userドキュメント作成（email 未指定時はフィールドを保存しない）
    const userDoc: any = {
      username,
      password: hashedPassword,
      displayName,
      anonId
    };
    if (email) userDoc.email = email;
    const user = await UserModel.create(userDoc);

    // UserMeta初期化（既存があれば上書きしない）
    const existingMeta = await UserMetaModel.findOne({ anonId });
    if (!existingMeta) {
      await UserMetaModel.create({
        anonId,
        lotteryBonusCount: 0,
        cardsAlbum: [],
        displayName
      });
    }

    // JWTトークン生成
    const token = jwt.sign(
      { userId: String(user._id), email: user.email || null, username: user.username || null },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    // HttpOnly Cookie設定
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7日
    });

    logger.info('auth.register.success', { email: user.email, userId: String(user._id) });

    return res.status(201).json({
      ok: true,
      user: {
        id: String(user._id),
        email: user.email,
        username: user.username,
        displayName: user.displayName,
        anonId: user.anonId
      }
    });
  } catch (err) {
    next(err);
  }
});

// ログイン
authRouter.post('/auth/login', async (req, res, next) => {
  try {
    const parsed = LoginSchema.parse(req.body);

    // ユーザー検索（email or username）
    let user = null as any;
    if (parsed.email) user = await UserModel.findOne({ email: parsed.email.toLowerCase() });
    if (!user && parsed.username) user = await UserModel.findOne({ username: parsed.username.toLowerCase() });
    if (!user) {
      throw new UnauthorizedError('Invalid email or password');
    }

    // パスワード検証
    const isValid = await bcrypt.compare(parsed.password, user.password);
    if (!isValid) {
      throw new UnauthorizedError('Invalid email or password');
    }

    // 互換: UserMeta.displayName が空なら username を既定値として補完
    try {
      const meta = await UserMetaModel.findOne({ anonId: user.anonId });
      const shouldFill = !meta || !(meta as any).displayName || String((meta as any).displayName).trim() === '';
      if (shouldFill) {
        const newName = (user.username || '').trim();
        if (newName) {
          if (meta) {
            (meta as any).displayName = newName;
            await (meta as any).save();
          } else {
            await UserMetaModel.create({ anonId: user.anonId, lotteryBonusCount: 0, cardsAlbum: [], displayName: newName });
          }
        }
      }
    } catch {}

    // JWTトークン生成
    const token = jwt.sign(
      { userId: String(user._id), email: user.email || null, username: user.username || null },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    // HttpOnly Cookie設定
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000
    });

    logger.info('auth.login.success', { email: user.email, userId: String(user._id) });

    return res.json({
      ok: true,
      user: {
        id: String(user._id),
        email: user.email,
        username: user.username,
        displayName: user.displayName,
        anonId: user.anonId
      }
    });
  } catch (err) {
    next(err);
  }
});

// ログアウト
authRouter.post('/auth/logout', async (req, res, next) => {
  try {
    res.clearCookie('token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    });

    logger.info('auth.logout');
    return res.json({ ok: true, message: 'Logged out successfully' });
  } catch (err) {
    next(err);
  }
});

// 現在のユーザー取得
authRouter.get('/auth/me', async (req, res, next) => {
  try {
    const token = req.cookies?.token || 
      (req.headers.authorization?.startsWith('Bearer ') ? req.headers.authorization.slice(7) : null);

    if (!token) {
      return res.json({ ok: false, user: null });
    }

    const decoded = jwt.verify(token, JWT_SECRET) as { userId: string; email: string };
    const user = await UserModel.findById(decoded.userId).select('-password');

    if (!user) {
      return res.json({ ok: false, user: null });
    }

    return res.json({
      ok: true,
      user: {
        id: String(user._id),
        email: user.email,
        displayName: user.displayName,
        anonId: user.anonId
      }
    });
  } catch (err) {
    return res.json({ ok: false, user: null });
  }
});

