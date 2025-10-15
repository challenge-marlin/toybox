import mongoose, { Schema, Document, Model } from 'mongoose';

export interface JackpotWin extends Document {
  anonId: string;
  displayName?: string;
  createdAt: Date;
}

const JackpotWinSchema = new Schema<JackpotWin>(
  {
    anonId: { type: String, required: true, index: true },
    displayName: { type: String },
    createdAt: { type: Date, default: () => new Date(), required: true }
  },
  { timestamps: { createdAt: true, updatedAt: false } }
);

export const JackpotWinModel: Model<JackpotWin> =
  mongoose.models.JackpotWin || mongoose.model<JackpotWin>('JackpotWin', JackpotWinSchema);


