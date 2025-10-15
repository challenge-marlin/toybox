import { Queue } from 'bullmq';

const connection = { connection: { url: process.env.REDIS_URL || 'redis://127.0.0.1:6379' } } as any;

export const notificationQueue = new Queue('notification', connection);

export type NotificationJob = {
  anonId: string;
  message: string;
  title?: string;
  cardId?: string;
};

export async function enqueueNotification(job: NotificationJob) {
  await notificationQueue.add('notify', job, { removeOnComplete: true, attempts: 3, backoff: 5000 });
}
