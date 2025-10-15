export interface FeedItemDto {
  id: string;
  anonId: string;
  displayName: string | null;
  createdAt: Date;
  imageUrl: string | null;
  avatarUrl: string | null;
  displayImageUrl: string | null; // 表示用画像URL（post.imageUrl 優先、無ければ author.avatarUrl）
  title: string | null;
}

export interface FeedResponseDto {
  items: FeedItemDto[];
  nextCursor: Date | null;
}

export interface SubmissionItemDto {
  id: string;
  createdAt: Date;
  imageUrl: string | null;
  displayImageUrl: string | null; // 表示用画像URL（post.imageUrl 優先、無ければ author.avatarUrl）
}

export interface SubmissionsResponseDto {
  items: SubmissionItemDto[];
  nextCursor?: Date | null;
}

