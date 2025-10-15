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
  createdAt: Date;
  updatedAt: Date;
}

const CardEntrySchema = new Schema<CardEntry>(
  {
    id: { type: String, required: true },
    obtainedAt: { type: Date }
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
    headerUrl: { type: String }
  },
  {
    timestamps: true
  }
);

UserMetaSchema.index({ anonId: 1 });

export const UserMetaModel: Model<UserMeta> =
  mongoose.models.UserMeta || mongoose.model<UserMeta>('UserMeta', UserMetaSchema);
