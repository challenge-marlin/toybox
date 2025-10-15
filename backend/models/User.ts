import mongoose, { Schema, Document, Model } from 'mongoose';

export interface User extends Document {
  email?: string;
  password: string; // bcryptハッシュ
  displayName?: string;
  anonId: string; // UserMetaと紐づけ用
  username?: string; // ログインID（任意、ユニーク）
  createdAt: Date;
  updatedAt: Date;
}

const UserSchema = new Schema<User>(
  {
    email: {
      type: String,
      required: false,
      index: true,
      lowercase: true,
      trim: true
    },
    password: { 
      type: String, 
      required: true 
    },
    displayName: { 
      type: String,
      maxlength: 50
    },
    anonId: { 
      type: String, 
      required: true,
      index: true
    },
    username: {
      type: String,
      lowercase: true,
      trim: true,
      minlength: 3,
      maxlength: 30
    }
  },
  {
    timestamps: true
  }
);

// 部分インデックス: 値が存在する場合のみユニーク制約を適用
UserSchema.index(
  { email: 1 },
  { unique: true, partialFilterExpression: { email: { $exists: true, $type: 'string' } } }
);
UserSchema.index(
  { username: 1 },
  { unique: true, partialFilterExpression: { username: { $exists: true, $type: 'string' } } }
);

export const UserModel: Model<User> =
  mongoose.models.User || mongoose.model<User>('User', UserSchema);

