import mongoose, { Schema } from 'mongoose';
const SubmissionSchema = new Schema({
    submitterAnonId: { type: String, required: true, index: true },
    aim: { type: String, required: true, maxlength: 100 },
    steps: {
        type: [String],
        validate: {
            validator: (arr) => Array.isArray(arr) && arr.length === 3,
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
    createdAt: { type: Date, default: () => new Date() },
    updatedAt: { type: Date, default: () => new Date() }
}, {
    timestamps: true
});
SubmissionSchema.pre('save', function (next) {
    this.updatedAt = new Date();
    next();
});
export const SubmissionModel = mongoose.models.Submission || mongoose.model('Submission', SubmissionSchema);
//# sourceMappingURL=Submission.js.map