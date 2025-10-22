import { Router } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { UserModel } from '../../models/User.js';
import { UserMetaModel } from '../../models/UserMeta.js';
import { BadRequestError, UnauthorizedError } from '../middleware/errorHandler.js';
import { SubmissionModel } from '../../models/Submission.js';
import { logger } from '../utils/logger.js';

export const authRouter = Router();

const JWT_SECRET = process.env.JWT_SECRET || 'change_me_strong_secret';
const BCRYPT_ROUNDS = 12;

// バリデーションスキーマ
const RegisterSchema = z.object({
  // email は当面不要
  // username は必須（3-30, 英数_）
  username: z.string().min(3).max(30).regex(/^[a-z0-9_]+$/i),
  password: z.string().min(8).max(128),
  displayName: z.string().min(1).max(50)
});

const LoginSchema = z.object({
  email: z.string().email().optional(),
  username: z.string().min(3).max(30).regex(/^[a-z0-9_]+$/i).optional(),
  password: z.string()
}).refine((data) => !!data.email || !!data.username, {
  message: 'email or username is required'
});

// 登録（ID/表示名/パスワード）
authRouter.post('/auth/register', async (req, res, next) => {
  try {
    const parsed = RegisterSchema.parse(req.body);
    const email = undefined as any;
    const rawUsername = parsed.username?.toLowerCase();

    // 既存ユーザーチェック
    if (rawUsername) {
      const existingUsername = await UserModel.findOne({ username: rawUsername });
      if (existingUsername) throw new BadRequestError('Username already taken');
    }

    // パスワードハッシュ
    const hashedPassword = await bcrypt.hash(parsed.password, BCRYPT_ROUNDS);

    // username は必須入力
    const username = rawUsername!;

    // anonId は username と同一にする
    const anonId = username;
    // displayName が未指定の場合は username を既定値にする
    const displayName = parsed.displayName.trim();

    // Userドキュメント作成（email 未指定時はフィールドを保存しない）
    const userDoc: any = {
      username,
      password: hashedPassword,
      displayName,
      anonId
    };
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

// Discord OAuth: リダイレクト開始
authRouter.get('/auth/discord/login', async (req, res) => {
  const clientId = (process.env.DISCORD_CLIENT_ID || '').trim();
  const redirectUri = (process.env.DISCORD_REDIRECT_URI || '').trim();
  const scope = 'identify';
  const isSnowflake = /^\d{17,20}$/.test(clientId);
  if (!clientId || !isSnowflake || !redirectUri) {
    return res.status(500).json({
      error: 'Discord OAuth is not configured correctly',
      hint: 'Set DISCORD_CLIENT_ID (numeric) and DISCORD_REDIRECT_URI in backend/.env and restart the backend.',
      received: { DISCORD_CLIENT_ID: clientId || null, DISCORD_REDIRECT_URI: redirectUri || null }
    });
  }
  const url = new URL('https://discord.com/api/oauth2/authorize');
  url.searchParams.set('client_id', clientId);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('scope', scope);
  res.redirect(url.toString());
});

// Discord OAuth: コールバック
authRouter.get('/auth/discord/callback', async (req, res, next) => {
  try {
    const code = String(req.query.code || '');
    const clientId = process.env.DISCORD_CLIENT_ID || '';
    const clientSecret = process.env.DISCORD_CLIENT_SECRET || '';
    const redirectUri = process.env.DISCORD_REDIRECT_URI || '';
    if (!code || !clientId || !clientSecret || !redirectUri) throw new BadRequestError('OAuth config missing');

    const tokenRes = await fetch('https://discord.com/api/oauth2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirectUri
      })
    });
    if (!tokenRes.ok) throw new BadRequestError('Failed to exchange code');
    const tokenJson: any = await tokenRes.json();
    const accessToken = tokenJson.access_token as string;
    if (!accessToken) throw new BadRequestError('Invalid access token');

    const meRes = await fetch('https://discord.com/api/users/@me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    });
    if (!meRes.ok) throw new BadRequestError('Failed to fetch user profile');
    const me: any = await meRes.json();
    const discordId = String(me.id);
    const discordName = String(me.global_name || me.username || `user-${discordId}`);

    // username を discord_ + id で一意化
    const username = `discord_${discordId}`;
    const anonId = username;
    const displayName = discordName.slice(0, 50);

    let user = await UserModel.findOne({ username });
    if (!user) {
      // ランダムパスワード（使われないが必須フィールドのため保存）
      const randomPass = await bcrypt.hash(`discord_${discordId}_${Math.random().toString(36).slice(2)}`, BCRYPT_ROUNDS);
      user = await UserModel.create({ username, password: randomPass, displayName, anonId });
      const existingMeta = await UserMetaModel.findOne({ anonId });
      if (!existingMeta) {
        await UserMetaModel.create({ anonId, lotteryBonusCount: 0, cardsAlbum: [], displayName });
      }
    } else {
      // 表示名を最新に同期（任意）
      try {
        user.displayName = displayName;
        await user.save();
        const meta = await UserMetaModel.findOne({ anonId });
        if (meta) { (meta as any).displayName = displayName; await (meta as any).save(); }
      } catch {}
    }

    // JWT
    const token = jwt.sign(
      { userId: String(user._id), email: user.email || null, username: user.username || null },
      JWT_SECRET,
      { expiresIn: '7d' }
    );
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000
    });
    res.redirect('/mypage');
  } catch (err) {
    next(err);
  }
});

// アカウント削除
authRouter.post('/auth/deleteAccount', async (req, res, next) => {
  try {
    const token = req.cookies?.token || (req.headers.authorization?.startsWith('Bearer ') ? req.headers.authorization.slice(7) : null);
    if (!token) throw new UnauthorizedError('Not logged in');
    const decoded = jwt.verify(token, JWT_SECRET) as { userId: string };
    const user = await UserModel.findById(decoded.userId).lean();
    if (!user) throw new UnauthorizedError('User not found');
    const anonId = (user as any).anonId as string;

    // 関連データ削除
    await SubmissionModel.deleteMany({ submitterAnonId: anonId });
    await UserMetaModel.deleteOne({ anonId });
    await UserModel.deleteOne({ _id: decoded.userId });

    // セッションクリア
    res.clearCookie('token', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' });
    return res.json({ ok: true });
  } catch (err) {
    next(err);
  }
});

