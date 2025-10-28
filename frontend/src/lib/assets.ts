// NOTE: Frontend uses backend REST; for server route we would normally run on Next server.
// Here we provide a helper to resolve an Asset from existing feed/submission endpoints by id.

export type Asset = {
	id: string;
	type: 'image' | 'video' | 'game' | 'other';
	title?: string;
	authorName?: string;
	mimeType: string;
	sizeBytes?: number;
	fileUrl: string;
};

function getBaseUrl(): string {
	const isServer = typeof window === 'undefined';
	if (isServer) {
		return process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:4000';
	}
	return process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:4000';
}

export function resolveUploadUrl(u?: string | null): string | undefined {
	if (!u) return undefined;
	const base = getBaseUrl();
	if (u.startsWith('/uploads/')) return `${base}${u}`;
	return u;
}

// Best-effort implementation: page through /api/feed to find the item
export async function getAssetById(assetId: string): Promise<Asset | null> {
	const base = getBaseUrl();
	let cursor: string | null = null;
	for (let i = 0; i < 5; i++) { // search up to 5 pages
		const url = `${base}/api/feed?limit=50${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`;
		const res = await fetch(url, { cache: 'no-store' });
		if (!res.ok) break;
		const data: any = await res.json();
		const items: any[] = Array.isArray(data?.items) ? data.items : [];
		const hit = items.find((it) => String(it.id) === String(assetId));
		if (hit) {
			const fileUrl = resolveUploadUrl(hit.videoUrl || hit.imageUrl || hit.displayImageUrl);
			if (!fileUrl) return null;
			const type: Asset['type'] = hit.videoUrl ? 'video' : (hit.imageUrl ? 'image' : (hit.gameUrl ? 'game' : 'other'));
			return {
				id: String(hit.id),
				type,
				title: hit.title || undefined,
				authorName: hit.displayName || hit.anonId || undefined,
				mimeType: hit.videoUrl ? 'video/mp4' : 'image/png',
				fileUrl
			};
		}
		cursor = data?.nextCursor ?? null;
		if (!cursor) break;
	}
	return null;
}


