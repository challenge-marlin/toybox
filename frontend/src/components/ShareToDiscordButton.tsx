'use client';
import React, { useState } from 'react';

export type Asset = {
	id: string;
	type: 'image' | 'video' | 'game' | 'other';
	title?: string;
	authorName?: string;
	mimeType: string;
	sizeBytes?: number;
	fileUrl: string;
};

function isShareable(asset: Asset): boolean {
	return asset.type === 'image' || asset.type === 'video';
}

export function ShareToDiscordButton({ asset }: { asset: Asset }) {
	const [loading, setLoading] = useState(false);
	const [lastMessageId, setLastMessageId] = useState<string | null>(null);

	if (!isShareable(asset)) return null;

	async function onClick() {
		try {
			setLoading(true);
			setLastMessageId(null);
			const res = await fetch('/api/share/discord', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ assetId: asset.id })
			});
			const data = await res.json();
			if (!res.ok || !data?.ok) {
				const msg = String(data?.error || '共有に失敗しました');
				if (msg.includes('20MB')) {
					alert('20MBを超えるため、Discordに直接投稿できません。圧縮するか外部リンクを共有してください。');
				} else {
					alert(msg);
				}
				return;
			}
			setLastMessageId(String(data.discordMessageId || ''));
			alert('Discordにシェアしました');
		} catch (e: any) {
			const msg = e?.message?.includes('20MB')
				? '20MBを超えるため、Discordに直接投稿できません。圧縮するか外部リンクを共有してください。'
				: (e?.message || '共有に失敗しました');
			alert(msg);
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className="flex items-center gap-2">
			<button
				onClick={onClick}
				disabled={loading}
				className="inline-flex items-center gap-2 rounded-xl px-4 py-2 shadow-sm border bg-white hover:bg-gray-50 disabled:opacity-60"
				aria-label="Discordにシェア"
			>
				{loading ? (
					<span>送信中…</span>
				) : (
					<span className="inline-flex items-center gap-2">
						<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-[#5865F2]"><path d="M20.317 4.369A19.791 19.791 0 0 0 16.558 3c-.2.363-.43.85-.59 1.23a18.33 18.33 0 0 0-5.934 0A9.145 9.145 0 0 0 9.464 3a19.736 19.736 0 0 0-3.759 1.369C2.83 8.165 2.18 11.86 2.454 15.5a19.9 19.9 0 0 0 4.883 2.469c.395-.54.747-1.11 1.053-1.706a12.7 12.7 0 0 1-1.66-.8c.14-.103.277-.211.408-.322 3.219 1.5 6.711 1.5 9.896 0 .133.111.27.219.41.322-.53.31-1.09.583-1.668.8.306.596.658 1.166 1.053 1.706a19.9 19.9 0 0 0 4.882-2.469c.4-5.09-.683-8.753-2.524-11.131ZM9.861 13.623c-.96 0-1.748-.88-1.748-1.957 0-1.078.77-1.958 1.748-1.958.978 0 1.766.88 1.748 1.958 0 1.078-.77 1.957-1.748 1.957Zm4.295 0c-.96 0-1.748-.88-1.748-1.957 0-1.078.77-1.958 1.748-1.958s1.748.88 1.748 1.958c0 1.078-.77 1.957-1.748 1.957Z"/></svg>
						<span>Discordにシェア</span>
					</span>
				)}
			</button>
			{lastMessageId ? (
				<a
					href={`https://discord.com/channels/@me`}
					target="_blank"
					rel="noreferrer"
					className="text-sm text-[#5865F2] underline"
				>
					Discordで開く
				</a>
			) : null}
		</div>
	);
}



