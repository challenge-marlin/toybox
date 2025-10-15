import { Worker } from 'bullmq';
import { logger } from '../utils/logger.js';

const connection = { connection: { url: process.env.REDIS_URL || 'redis://127.0.0.1:6379' } } as any;

const worker = new Worker(
  'notification',
  async (job) => {
    const { anonId, message, title, cardId } = job.data as any;
    logger.info('notification.process', { anonId, title: title ?? '-', cardId: cardId ?? '-', message });
  },
  connection
);

worker.on('completed', (job) => {
  logger.info('notification.completed', { jobId: job.id });
});

worker.on('failed', (job, err) => {
  logger.error('notification.failed', { jobId: job?.id, error: String(err?.message || err) });
});
