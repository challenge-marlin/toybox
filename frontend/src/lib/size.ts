export const MAX_DISCORD_FILE_SIZE = 20 * 1024 * 1024; // 20MB

export function isShareableMime(mime: string | undefined | null): boolean {
	if (!mime) return false;
	return mime.startsWith('image/') || mime.startsWith('video/');
}

export async function getContentLength(url: string, opts?: { headers?: HeadersInit }): Promise<number | null> {
	try {
		const head = await fetch(url, { method: 'HEAD', headers: opts?.headers });
		if (!head.ok) return null;
		const len = head.headers.get('content-length');
		return len ? Number(len) : null;
	} catch {
		return null;
	}
}

export async function getContentType(url: string, opts?: { headers?: HeadersInit }): Promise<string | null> {
	try {
		const head = await fetch(url, { method: 'HEAD', headers: opts?.headers });
		if (!head.ok) return null;
		return head.headers.get('content-type');
	} catch {
		return null;
	}
}

export function getExtensionFromMime(mime: string | undefined | null): string {
	if (!mime) return '.bin';
	const m = mime.toLowerCase();
	if (m === 'image/png') return '.png';
	if (m === 'image/jpeg' || m === 'image/jpg') return '.jpg';
	if (m === 'image/webp') return '.webp';
	if (m === 'image/gif') return '.gif';
	if (m === 'video/mp4') return '.mp4';
	if (m === 'video/webm') return '.webm';
	if (m === 'video/quicktime' || m === 'video/mov') return '.mov';
	return '.bin';
}

export function slugifyBaseName(input: string): string {
	const base = (input || 'upload').trim();
	return base.replace(/[^\w\-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'upload';
}

export function getFilenameFromAsset(asset: { title?: string; mimeType?: string | null; id: string }): string {
	const base = slugifyBaseName(asset.title || asset.id);
	return `${base}${getExtensionFromMime(asset.mimeType || null)}`;
}

export function isShareableAsset(asset: { type: string; mimeType?: string | null }): boolean {
	if (!(asset && (asset.type === 'image' || asset.type === 'video'))) return false;
	return isShareableMime(asset.mimeType || 'image/*');
}



