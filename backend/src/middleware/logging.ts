import type { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger.js';

export function requestLogger(req: Request, _res: Response, next: NextFunction) {
  const start = Date.now();
  const { method, url } = req;
  (req as any)._startAt = start;
  logger.info('request.start', { method, url });
  next();
}

export function responseTimeLogger(req: Request, res: Response, next: NextFunction) {
  const after = () => {
    const start = (req as any)._startAt as number | undefined;
    const ms = start ? Date.now() - start : undefined;
    logger.info('request.end', { method: req.method, url: req.url, status: res.statusCode, ms });
  };
  res.on('finish', after);
  res.on('close', after);
  next();
}

export function errorHandler(err: any, req: Request, res: Response, _next: NextFunction) {
  logger.error('request.error', { method: req.method, url: req.url, error: String(err?.message || err) });
  res.status(500).json({ error: 'Internal Server Error' });
}
