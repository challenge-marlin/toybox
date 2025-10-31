import Link from 'next/link';

function getApiBase() {
  return process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:4000';
}

async function fetchDetail(id: string) {
  const base = getApiBase();
  const res = await fetch(`${base}/api/submissions/${encodeURIComponent(id)}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({ params }: { params: { id: string } }) {
  const d = await fetchDetail(params.id);
  if (!d) return { title: '投稿が見つかりません' };
  const title = d.displayName ? `${d.displayName} の投稿` : `投稿 ${d.id}`;
  const description = d.displayName ? `${d.displayName} さんの投稿（${new Date(d.createdAt).toLocaleString()}）` : `投稿ID: ${d.id}`;
  const base = getApiBase();
  const image = d.displayImageUrl ? (String(d.displayImageUrl).startsWith('/uploads/') ? `${base}${d.displayImageUrl}` : d.displayImageUrl) : undefined;
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      images: image ? [{ url: image }] : undefined,
    },
    alternates: { canonical: `/s/${encodeURIComponent(params.id)}` },
  };
}

export default async function SubmissionDetailPage({ params }: { params: { id: string } }) {
  const d = await fetchDetail(params.id);
  const base = getApiBase();
  if (!d) {
    return (
      <main className="mx-auto max-w-3xl p-4">
        <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">投稿詳細</h1>
        <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-4 text-steam-iron-200">投稿が見つかりませんでした。</div>
        <div className="mt-4"><Link href="/feed" className="text-steam-gold-300 underline">フィードへ戻る</Link></div>
      </main>
    );
  }

  const displayUrl: string | undefined = d.displayImageUrl
    ? (String(d.displayImageUrl).startsWith('/uploads/') ? `${base}${d.displayImageUrl}` : d.displayImageUrl)
    : undefined;
  const videoUrl: string | undefined = d.videoUrl
    ? (String(d.videoUrl).startsWith('/uploads/') ? `${base}${d.videoUrl}` : d.videoUrl)
    : undefined;
  const imageUrl: string | undefined = d.imageUrl
    ? (String(d.imageUrl).startsWith('/uploads/') ? `${base}${d.imageUrl}` : d.imageUrl)
    : undefined;
  const gameUrl: string | undefined = d.gameUrl
    ? (String(d.gameUrl).startsWith('/uploads/') ? `${base}${d.gameUrl}` : d.gameUrl)
    : undefined;

  return (
    <main className="mx-auto max-w-3xl p-4">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">投稿詳細</h1>
      <div className="rounded border border-steam-iron-700 bg-steam-iron-900 p-4">
        {/* JSON-LD 構造化データ */}
        {(() => {
          const data = d ? (videoUrl ? {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            name: d.title || (d.displayName ? `${d.displayName} の動画` : `動画 ${d.id}`),
            uploadDate: d.createdAt,
            thumbnailUrl: displayUrl || imageUrl || undefined,
            contentUrl: videoUrl
          } : {
            "@context": "https://schema.org",
            "@type": "ImageObject",
            name: d.title || (d.displayName ? `${d.displayName} の画像` : `画像 ${d.id}`),
            uploadDate: d.createdAt,
            contentUrl: imageUrl || displayUrl
          }) : null;
          return data ? (
            <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />
          ) : null;
        })()}
        <div className="flex items-center gap-3 mb-4">
          <div className="h-12 w-12 overflow-hidden rounded-full border border-steam-iron-700 bg-steam-iron-800 flex items-center justify-center text-xs text-steam-iron-400">
            {d.avatarUrl ? (
              <img src={String(d.avatarUrl).startsWith('/uploads/') ? `${base}${d.avatarUrl}` : d.avatarUrl} alt="avatar" className="h-full w-full object-cover" />
            ) : (
              <span>{String(d.anonId || '').slice(0,2).toUpperCase()}</span>
            )}
          </div>
          <div>
            <div className="text-steam-iron-100 font-semibold">{d.displayName || d.anonId || '—'}</div>
            <div className="text-xs text-steam-iron-300">{new Date(d.createdAt).toLocaleString()}</div>
          </div>
        </div>

        <div className="w-full flex items-center justify-center">
          {gameUrl ? (
            <a href={gameUrl} target="_blank" rel="noreferrer" className="text-steam-gold-300 underline">ゲームを開く</a>
          ) : videoUrl ? (
            <video src={videoUrl} className="max-w-full rounded" controls preload="metadata" />
          ) : imageUrl ? (
            <img src={imageUrl} alt="submission" className="max-w-full rounded" />
          ) : displayUrl ? (
            <img src={displayUrl} alt="submission" className="max-w-full rounded" />
          ) : (
            <div className="text-steam-iron-300 text-sm">画像/動画がありません</div>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <Link href="/feed" className="text-steam-gold-300 underline">フィードへ</Link>
          <div className="flex items-center gap-2">
            {d.prevId && <Link href={`/s/${encodeURIComponent(d.prevId)}`} className="text-steam-iron-200 hover:underline">← 前へ</Link>}
            {d.nextId && <Link href={`/s/${encodeURIComponent(d.nextId)}`} className="text-steam-iron-200 hover:underline">次へ →</Link>}
          </div>
        </div>
      </div>
    </main>
  );
}
