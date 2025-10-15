import type { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { UnauthorizedError } from './errorHandler.js';
import { incUnauthorized401 } from '../utils/metrics.js';

const JWT_SECRET = process.env.JWT_SECRET || 'change_me_strong_secret';

export interface AuthenticatedRequest extends Request {
  userId?: string;
  userEmail?: string;
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  // Preflight は認証不要で通す
  if (req.method === 'OPTIONS') return next();

  // Cookie または Authorization ヘッダーからトークンを取得
  const token = req.cookies?.token || 
    (req.headers.authorization?.startsWith('Bearer ') ? req.headers.authorization.slice(7) : null);

  if (!token) {
    incUnauthorized401();
    return next(new UnauthorizedError('Authentication required'));
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET) as { userId: string; email: string };
    (req as AuthenticatedRequest).userId = decoded.userId;
    (req as AuthenticatedRequest).userEmail = decoded.email;
    next();
  } catch (err) {
    incUnauthorized401();
    return next(new UnauthorizedError('Invalid or expired token'));
  }
}

// Optional auth: トークンがあればデコード、なければスキップ
export function optionalAuth(req: Request, res: Response, next: NextFunction) {
  const token = req.cookies?.token || 
    (req.headers.authorization?.startsWith('Bearer ') ? req.headers.authorization.slice(7) : null);

  if (token) {
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as { userId: string; email: string };
      (req as AuthenticatedRequest).userId = decoded.userId;
      (req as AuthenticatedRequest).userEmail = decoded.email;
    } catch {
      // トークン無効でもエラーにしない
    }
  }
  next();
}

