import type { CardEntry } from '../../models/UserMeta.js';

export interface UserMeDto {
  anonId: string;
  activeTitle: string | null;
  activeTitleUntil: Date | null;
  cardsAlbum: CardEntry[];
  lotteryBonusCount: number;
}

export interface UserProfileDto {
  anonId: string;
  activeTitle: string | null;
  activeTitleUntil: Date | null;
  displayName: string;
  avatarUrl: string | null;
  headerUrl: string | null;
  bio: string;
  cardsAlbum: CardEntry[];
  updatedAt: Date | null;
}

export interface UpdateProfileResponse {
  ok: boolean;
  bio?: string;
  displayName?: string;
  avatarUrl?: string;
  headerUrl?: string;
}

