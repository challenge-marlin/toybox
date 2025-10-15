import mongoose, { Schema } from 'mongoose';
const CardEntrySchema = new Schema({
    id: { type: String, required: true },
    obtainedAt: { type: Date }
}, { _id: false });
const UserMetaSchema = new Schema({
    anonId: { type: String, required: true, index: true, unique: true },
    lotteryBonusCount: { type: Number, required: true, min: 0, default: 0 },
    cardsAlbum: { type: [CardEntrySchema], default: [] },
    activeTitle: { type: String },
    activeTitleUntil: { type: Date }
}, {
    timestamps: true
});
UserMetaSchema.index({ anonId: 1 });
export const UserMetaModel = mongoose.models.UserMeta || mongoose.model('UserMeta', UserMetaSchema);
//# sourceMappingURL=UserMeta.js.map