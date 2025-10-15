import type { Request, Response, NextFunction } from 'express';
import { UserModel } from '../../models/User.js';
import { incUnauthorized401 } from '../utils/metrics.js';

export async function requireAnonAuth(req: Request, res: Response, next: NextFunction) {
  // Preflight は認証不要で通す
  if (req.method === 'OPTIONS') return next();
  // x-anon-id などのヘッダは廃止
  let anonId: string | undefined;

  // optionalAuth により userId が付与されていれば、それ経由で anonId を解決
  if (!anonId && (req as any).userId) {
    try {
      const user = await UserModel.findById((req as any).userId).lean();
      anonId = (user as any)?.anonId || undefined;
    } catch {}
  }

  if (!anonId) {
    incUnauthorized401();
    return res.status(401).json({ error: 'Unauthorized' });
  }
  (req as any).anonId = anonId;
  next();
}
