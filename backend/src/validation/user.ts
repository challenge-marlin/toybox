import { z } from 'zod';

export const UpdateBioSchema = z.object({
  bio: z.string().max(160).optional().default('')
});

export const UpdateDisplayNameSchema = z.object({
  displayName: z.string().min(1).max(50)
});

export const UploadKindSchema = z.object({
  kind: z.enum(['avatar', 'header']).default('avatar')
});

export type UpdateBioInput = z.infer<typeof UpdateBioSchema>;
export type UpdateDisplayNameInput = z.infer<typeof UpdateDisplayNameSchema>;
export type UploadKindInput = z.infer<typeof UploadKindSchema>;

