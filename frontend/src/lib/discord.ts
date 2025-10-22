const API = 'https://discord.com/api/v10';

type PostArgs = { buffer: ArrayBuffer; filename: string; caption: string };

type PostResult = { ok: true; messageId: string } | { ok: false; status?: number; error: string };

function getEnv(): { CHANNEL_ID: string | undefined; BOT: string | undefined } {
	return {
		CHANNEL_ID: process.env.DISCORD_CHANNEL_ID,
		BOT: process.env.DISCORD_BOT_TOKEN
	};
}

export async function postToDiscord({ buffer, filename, caption }: PostArgs): Promise<PostResult> {
	const { CHANNEL_ID, BOT } = getEnv();
	if (!CHANNEL_ID || !BOT) return { ok: false, status: 500, error: 'Missing Discord env' };

	const buildForm = () => {
		const f = new FormData();
		f.append('payload_json', JSON.stringify({ content: caption.slice(0, 300).replace(/\n+/g, ' ') }));
		const blob = new Blob([buffer]);
		// @ts-ignore filename is supported in undici FormData
		f.append('files[0]', blob, filename);
		return f;
	};

	async function tryPost(): Promise<Response> {
		const form = buildForm();
		return await fetch(`${API}/channels/${CHANNEL_ID}/messages`, {
			method: 'POST',
			headers: { Authorization: `Bot ${BOT}` },
			body: form
		});
	}

	let res: Response;
	try {
		res = await tryPost();
	} catch (e: any) {
		return { ok: false, error: `Network error: ${e?.message || 'fetch failed'}` };
	}

	if (res.status === 429) {
		let retryMs = 1000;
		try {
			const data: any = await res.json();
			retryMs = Math.min(Math.ceil(Number(data?.retry_after || 1) * 1000), 3000);
		} catch {}
		await new Promise((r) => setTimeout(r, retryMs));
		try {
			res = await tryPost();
		} catch (e: any) {
			return { ok: false, error: `Network error after retry: ${e?.message || 'fetch failed'}` };
		}
	}

	if (!res.ok) {
		let text: string;
		try { text = await res.text(); } catch { text = `HTTP ${res.status}`; }
		return { ok: false, status: res.status, error: text };
	}
	const json: any = await res.json();
	return { ok: true, messageId: String(json.id) };
}


