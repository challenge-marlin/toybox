import type { Request, Response, NextFunction } from 'express';
import { incRateLimited429 } from '../utils/metrics.js';

type Bucket = { count: number; resetAt: number };
const store = new Map<string, Bucket>();

export type RateLimitOptions = {
  windowMs: number;
  max: number;
  key?: (req: Request) => string;
};

function defaultKey(req: Request): string {
  const headerAnon = (req.headers['x-anon-id'] as string) || undefined;
  const anonId = (req as any).anonId as string | undefined;
  const useAnon = headerAnon || anonId;
  const ip = (req.headers['x-forwarded-for'] as string) || req.socket.remoteAddress || 'unknown';
  return useAnon ? `anon:${useAnon}` : `ip:${ip}`;
}

export function rateLimitByAnonOrIp(opts: RateLimitOptions) {
  const windowMs = Math.max(1000, opts.windowMs);
  const max = Math.max(1, opts.max);
  const keyFn = opts.key ?? defaultKey;

  return function (req: Request, res: Response, next: NextFunction) {
    const key = keyFn(req);
    const now = Date.now();
    const bucket = store.get(key);

    if (!bucket || bucket.resetAt <= now) {
      store.set(key, { count: 1, resetAt: now + windowMs });
      res.setHeader('X-RateLimit-Limit', String(max));
      res.setHeader('X-RateLimit-Remaining', String(max - 1));
      res.setHeader('X-RateLimit-Reset', String(Math.floor((now + windowMs) / 1000)));
      return next();
    }

    if (bucket.count < max) {
      bucket.count += 1;
      res.setHeader('X-RateLimit-Limit', String(max));
      res.setHeader('X-RateLimit-Remaining', String(max - bucket.count));
      res.setHeader('X-RateLimit-Reset', String(Math.floor(bucket.resetAt / 1000)));
      return next();
    }

    incRateLimited429();
    const retrySec = Math.max(0, Math.floor((bucket.resetAt - now) / 1000));
    res.setHeader('Retry-After', String(retrySec));
    res.status(429).json({ error: 'Too Many Requests' });
  };
}
