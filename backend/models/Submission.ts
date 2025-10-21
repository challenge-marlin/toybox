import mongoose, { Schema, Document, Model } from 'mongoose';

export type LotteryResult = 'win' | 'lose' | 'none';

export interface Submission extends Document {
  submitterAnonId: string; // 固定匿名ID
  aim: string; // ねらい（最大100字）
  steps: string[]; // 再現手順（3行）
  jpResult: LotteryResult; // 抽選結果
  frameType: string; // フレーム種別
  imageUrl?: string; // 提出画像の相対URL（/uploads/...）
  videoUrl?: string; // 提出動画の相対URL（/uploads/...）
  gameUrl?: string;  // 展開済みゲームの index.html への相対URL（/uploads/...）
  // 添付資料の要件にある全フィールド（必要に応じて拡張）
  // 例: 作成日時、タグ、添付リソースの参照など
  createdAt: Date;
  updatedAt: Date;
}

const SubmissionSchema = new Schema<Submission>(
  {
    submitterAnonId: { type: String, required: true, index: true },
    aim: { type: String, required: true, maxlength: 100 },
    steps: {
      type: [String],
      validate: {
        validator: (arr: string[]) => Array.isArray(arr) && arr.length === 3,
        message: 'steps must be an array of exactly 3 strings'
      },
      required: true
    },
    jpResult: {
      type: String,
      enum: ['win', 'lose', 'none'],
      default: 'none',
      required: true
    },
    frameType: { type: String, required: true },
    imageUrl: { type: String },
    videoUrl: { type: String },
    gameUrl: { type: String },
    createdAt: { type: Date, default: () => new Date() },
    updatedAt: { type: Date, default: () => new Date() }
  },
  {
    timestamps: true
  }
);

SubmissionSchema.pre('save', function (next) {
  this.updatedAt = new Date();
  next();
});

export const SubmissionModel: Model<Submission> =
  mongoose.models.Submission || mongoose.model<Submission>('Submission', SubmissionSchema);
