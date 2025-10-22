import mongoose, { Schema, Document, Model } from 'mongoose';

export interface CardEntry {
  id: string; // カードID
  obtainedAt?: Date; // 入手日時
}

export interface UserMeta extends Document {
  anonId: string; // 固定匿名ID
  lotteryBonusCount: number; // 抽選ボーナス回数（未当選の連続回数として運用）
  cardsAlbum: CardEntry[]; // 所持カード一覧
  activeTitle?: string; // 称号
  activeTitleUntil?: Date; // 称号の有効期限（7日）
  displayName?: string; // 表示名
  bio?: string; // 自己紹介文
  avatarUrl?: string; // アイコン画像URL
  headerUrl?: string; // ヘッダー画像URL
  likedSubmissionIds?: string[]; // いいね済み投稿ID配列（文字列化されたObjectId）
  notifications?: NotificationEntry[]; // 通知
  createdAt: Date;
  updatedAt: Date;
}

export interface NotificationEntry {
  type: 'like';
  fromAnonId: string;
  submissionId: string;
  message: string;
  createdAt: Date;
  read?: boolean;
}

const CardEntrySchema = new Schema<CardEntry>(
  {
    id: { type: String, required: true },
    obtainedAt: { type: Date }
  },
  { _id: false }
);

const NotificationEntrySchema = new Schema<NotificationEntry>(
  {
    type: { type: String, enum: ['like'], required: true },
    fromAnonId: { type: String, required: true },
    submissionId: { type: String, required: true },
    message: { type: String, required: true },
    createdAt: { type: Date, required: true, default: () => new Date() },
    read: { type: Boolean, default: false }
  },
  { _id: false }
);

const UserMetaSchema = new Schema<UserMeta>(
  {
    anonId: { type: String, required: true, index: true, unique: true },
    lotteryBonusCount: { type: Number, required: true, min: 0, default: 0 },
    cardsAlbum: { type: [CardEntrySchema], default: [] },
    activeTitle: { type: String },
    activeTitleUntil: { type: Date },
    displayName: { type: String },
    bio: { type: String },
    avatarUrl: { type: String },
    headerUrl: { type: String },
    likedSubmissionIds: { type: [String], default: [] },
    notifications: { type: [NotificationEntrySchema], default: [] }
  },
  {
    timestamps: true
  }
);

UserMetaSchema.index({ anonId: 1 });

export const UserMetaModel: Model<UserMeta> =
  mongoose.models.UserMeta || mongoose.model<UserMeta>('UserMeta', UserMetaSchema);
