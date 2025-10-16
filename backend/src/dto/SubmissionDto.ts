export interface SubmissionResultDto {
  jpResult: 'win' | 'lose' | 'none';
  probability: number;
  bonusCount: number;
  rewardTitle?: string;
  rewardCardId?: string;
  rewardCard?: {
    card_id: string;
    card_name: string;
    rarity?: 'SSR' | 'SR' | 'R' | 'N';
    image_url?: string | null;
  };
  jackpotRecordedAt?: string | null;
}

