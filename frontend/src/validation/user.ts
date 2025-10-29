import { z } from 'zod';

export const UpdateBioSchema = z.object({
  bio: z.string().max(1000).optional().default('')
});

export const UpdateDisplayNameSchema = z.object({
  displayName: z.string().min(1).max(50)
});

export type UpdateBioInput = z.infer<typeof UpdateBioSchema>;
export type UpdateDisplayNameInput = z.infer<typeof UpdateDisplayNameSchema>;
