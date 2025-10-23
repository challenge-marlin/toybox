import { NextRequest, NextResponse } from 'next/server';
import { getContentLength, getFilenameFromAsset, isShareableMime, MAX_DISCORD_FILE_SIZE } from '../../../../lib/size';
import { postToDiscord } from '../../../../lib/discord';
import { getAssetById as getAssetByIdClient } from '../../../../lib/assets';

type Asset = {
	id: string;
	type: 'image' | 'video' | 'game' | 'other';
	title?: string;
	authorName?: string;
	mimeType: string; // e.g. image/png
	sizeBytes?: number;
	fileUrl: string;
};

// NOTE: For this ToyBox mono-repo, Next.js frontend is separate from Express backend.
// This route assumes assetId comes from backend DB; for demo, we call backend to resolve asset fields.

async function fetchAssetFromBackend(assetId: string): Promise<Asset | null> {
    // Use best-effort client helper to resolve from feed
    const a = await getAssetByIdClient(assetId);
    return a as Asset | null;
}

function sanitizeCaption(input: string): string {
	return input.replace(/[\r\n]+/g, ' ').slice(0, 300);
}

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
	// NOTE: In a full NextAuth setup, call getServerSession(). For this codebase, session is validated server-side by backend.
	try {
		const { assetId } = await req.json();
		if (!assetId) return NextResponse.json({ ok: false, error: 'assetId required' }, { status: 400 });

		const asset = await fetchAssetFromBackend(String(assetId));
		if (!asset) return NextResponse.json({ ok: false, error: 'asset not found' }, { status: 404 });
		if (!(asset.type === 'image' || asset.type === 'video')) {
			return NextResponse.json({ ok: false, error: 'asset type not shareable' }, { status: 400 });
		}
		if (!isShareableMime(asset.mimeType)) {
			return NextResponse.json({ ok: false, error: 'mime not allowed' }, { status: 400 });
		}

		let size = typeof asset.sizeBytes === 'number' ? asset.sizeBytes : await getContentLength(asset.fileUrl);
		if (size == null) {
			// If unknown, pessimistically reject
			size = MAX_DISCORD_FILE_SIZE + 1;
		}
		if (size > MAX_DISCORD_FILE_SIZE) {
			return NextResponse.json({ ok: false, error: 'File exceeds 20MB' }, { status: 400 });
		}

		const fileRes = await fetch(asset.fileUrl, { cache: 'no-store' });
		if (!fileRes.ok) return NextResponse.json({ ok: false, error: 'Failed to fetch file' }, { status: 502 });
		const arrayBuffer = await fileRes.arrayBuffer();
		const buffer = arrayBuffer;
		const filename = getFilenameFromAsset({ title: asset.title, mimeType: asset.mimeType, id: asset.id });
		const caption = sanitizeCaption(`ToyBoxからのシェア: ${asset.title ?? 'Untitled'} — by ${asset.authorName ?? 'unknown'}`);
		const r = await postToDiscord({ buffer, filename, caption });
        if (!('ok' in r) || !r.ok) return NextResponse.json(r, { status: (r as any).status ?? 502 });

		return NextResponse.json({ ok: true, discordMessageId: r.messageId });
	} catch (e: any) {
		return NextResponse.json({ ok: false, error: e?.message ?? 'Internal Error' }, { status: 500 });
	}
}


