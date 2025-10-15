export interface SubmissionResultDto {
  jpResult: 'win' | 'lose' | 'none';
  probability: number;
  bonusCount: number;
  rewardTitle?: string;
  rewardCardId?: string;
  jackpotRecordedAt?: string | null;
}

