import mongoose from 'mongoose';
import dotenv from 'dotenv';
import { SubmissionModel } from '../../models/Submission.js';

dotenv.config();

async function main() {
  const mongoUri = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/toybox';
  const dbName = process.env.MONGODB_DB || 'toybox';

  await mongoose.connect(mongoUri, { dbName } as any);

  // imageUrl を持つドキュメントのみ対象に $unset
  const res = await SubmissionModel.updateMany(
    { imageUrl: { $exists: true, $ne: null } },
    { $unset: { imageUrl: '' } }
  );

  console.log(`[clearSubmissionImages] matched=${res.matchedCount ?? (res as any).n ?? 0} modified=${res.modifiedCount ?? (res as any).nModified ?? 0}`);

  await mongoose.disconnect();
}

main().catch((err) => {
  console.error('[clearSubmissionImages] failed:', err);
  process.exit(1);
});


