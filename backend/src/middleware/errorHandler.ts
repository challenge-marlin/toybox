import type { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';
import { logger } from '../utils/logger.js';
import { incError, incUploadFailed } from '../utils/metrics.js';

export class AppError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(401, 'UNAUTHORIZED', message);
  }
}

export class BadRequestError extends AppError {
  constructor(message = 'Bad Request', details?: unknown) {
    super(400, 'BAD_REQUEST', message, details);
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Not Found') {
    super(404, 'NOT_FOUND', message);
  }
}

export class InternalServerError extends AppError {
  constructor(message = 'Internal Server Error') {
    super(500, 'INTERNAL_SERVER_ERROR', message);
  }
}

export function centralErrorHandler(err: unknown, req: Request, res: Response, _next: NextFunction) {
  // Multer file size error
  if (err && typeof err === 'object' && 'code' in err && err.code === 'LIMIT_FILE_SIZE') {
    incUploadFailed();
    logger.warn('upload.limit_exceeded', { method: req.method, url: req.url });
    return res.status(413).json({
      status: 413,
      code: 'PAYLOAD_TOO_LARGE',
      message: 'File size exceeds limit',
      details: null
    });
  }

  // Multer invalid file type (from fileFilter)
  if (err instanceof Error && err.message.includes('Invalid file type')) {
    incUploadFailed();
    logger.warn('upload.invalid_type', { method: req.method, url: req.url, error: err.message });
    return res.status(400).json({
      status: 400,
      code: 'INVALID_FILE_TYPE',
      message: err.message,
      details: null
    });
  }

  // Zod validation error
  if (err instanceof ZodError) {
    logger.warn('validation.failed', { method: req.method, url: req.url, issues: err.issues });
    return res.status(400).json({
      status: 400,
      code: 'VALIDATION_ERROR',
      message: 'Validation failed',
      details: err.issues
    });
  }

  // Custom AppError
  if (err instanceof AppError) {
    if (err.status >= 500) {
      incError();
      logger.error('request.error', { method: req.method, url: req.url, code: err.code, message: err.message });
    } else {
      logger.warn('request.client_error', { method: req.method, url: req.url, code: err.code, message: err.message });
    }
    return res.status(err.status).json({
      status: err.status,
      code: err.code,
      message: err.message,
      details: err.details || null
    });
  }

  // Mongoose validation error
  if (err && typeof err === 'object' && 'name' in err && err.name === 'ValidationError') {
    logger.warn('mongoose.validation', { method: req.method, url: req.url, error: String(err) });
    return res.status(400).json({
      status: 400,
      code: 'VALIDATION_ERROR',
      message: 'Database validation failed',
      details: err
    });
  }

  // Mongoose CastError (invalid ObjectId)
  if (err && typeof err === 'object' && 'name' in err && err.name === 'CastError') {
    logger.warn('mongoose.cast_error', { method: req.method, url: req.url, error: String(err) });
    return res.status(400).json({
      status: 400,
      code: 'INVALID_ID',
      message: 'Invalid ID format',
      details: null
    });
  }

  // Generic error
  incError();
  const message = err instanceof Error ? err.message : String(err);
  logger.error('request.error', { method: req.method, url: req.url, error: message });
  return res.status(500).json({
    status: 500,
    code: 'INTERNAL_SERVER_ERROR',
    message: 'Internal Server Error',
    details: null
  });
}

