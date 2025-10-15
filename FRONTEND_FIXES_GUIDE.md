# フロントエンド修正ガイド

## 実装状況

### ✅ バックエンド完成項目
1. **提出アップロード** - `POST /api/submit/upload` 実装済み
2. **プロフィールAPI** - `POST /api/user/profile/upload?type=avatar|header`, `PATCH /api/user/profile` 実装済み
3. **認証API** - `POST /api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `GET /api/auth/me` 実装済み

### 🔧 フロントエンド修正必要箇所

---

## タスクA: 提出アップロードの動作確認（mypage.tsx）

### 現状
- **`toybox-app/frontend/src/app/mypage/page.tsx:84`** で既に `/api/submit/upload` を呼び出し済み
- フィールド名は `file` で正しく設定されている

### 確認事項
✅ すでに正しく実装されています！

```tsx
const uploadRes = await fetch(`${API_BASE}/api/submit/upload`, {
  method: 'POST',
  body: form,  // FormData with 'file'
  headers: { 'Accept': 'application/json', ...(anonId ? { 'x-anon-id': anonId } : {}) }
});
```

### 動作確認
1. バックエンド起動: `cd toybox-app/backend && npm install && npm run dev`
2. フロントエンド起動: `cd toybox-app/frontend && npm run dev`
3. マイページで画像アップロード実行
4. 成功時に`rewards`オブジェクトと`imageUrl`が返却されることを確認

---

## タスクB: プロフィール反映修正

### 修正箇所1: `toybox-app/frontend/src/app/profile/page.tsx`

#### 現状の問題
- `saveName()` と `saveBio()` が個別API呼び出し
- 画像アップロードが`/api/user/profile/avatar`と`/api/user/profile/header`に分かれている

#### 推奨修正（オプション：統合エンドポイント利用）

既存のまま動作するはずですが、統合API `/api/user/profile/upload?type=avatar|header` を使う場合：

```tsx
async function upload(kind: 'avatar' | 'header', file: File) {
  try {
    const form = new FormData();
    form.append('file', file);
    
    const res = await fetch(`${API_BASE}/api/user/profile/upload?type=${kind}`, {
      method: 'POST',
      body: form,
      headers: { 'x-anon-id': getAnonId() || '' }
    });
    
    if (!res.ok) throw new Error('Upload failed');
    const data = await res.json();
    
    // キャッシュ対策で ?t= を付与
    const timestamp = Date.now();
    setProfile((p) => p ? {
      ...p,
      ...(kind === 'avatar' ? { avatarUrl: `${data.avatarUrl}?t=${timestamp}` } : {}),
      ...(kind === 'header' ? { headerUrl: `${data.headerUrl}?t=${timestamp}` } : {})
    } : p);
    
    setMsg(`${kind === 'avatar' ? 'アイコン' : 'ヘッダー'}を更新しました`);
    setTimeout(() => setMsg(null), 2000);
  } catch (err) {
    setMsg('アップロードに失敗しました');
  }
}
```

#### PATCH エンドポイント利用（推奨）

名前と自己紹介を同時更新する場合：

```tsx
async function saveProfile() {
  try {
    const payload: { displayName?: string; bio?: string } = {};
    if (name) payload.displayName = name;
    if (bio) payload.bio = bio;
    
    const res = await fetch(`${API_BASE}/api/user/profile`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'x-anon-id': getAnonId() || ''
      },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error('Update failed');
    const updatedUser = await res.json();
    
    setProfile((p) => p ? {
      ...p,
      displayName: updatedUser.displayName || p.displayName,
      // bioはUserMeDtoに含まれないため、個別APIで取得が必要
    } : p);
    
    setMsg('プロフィールを更新しました');
    setTimeout(() => setMsg(null), 2000);
  } catch (err) {
    setMsg('更新に失敗しました');
  }
}
```

---

## タスクC: サインアップ・ログイン画面実装

### 修正1: signup ページ新規作成

**ファイル**: `toybox-app/frontend/src/app/signup/page.tsx`

```tsx
'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, displayName }),
        credentials: 'include'
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || 'Registration failed');
      }

      // 登録成功 → トップページへ
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">アカウント作成</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-steam-gold-300">メールアドレス</label>
          <input 
            type="email" 
            required 
            className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm text-steam-gold-300">パスワード（8文字以上）</label>
          <input 
            type="password" 
            required 
            minLength={8}
            className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm text-steam-gold-300">表示名（任意）</label>
          <input 
            className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
            value={displayName} 
            onChange={(e) => setDisplayName(e.target.value)} 
          />
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button 
          disabled={loading} 
          className="rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400 disabled:opacity-50 w-full"
        >
          {loading ? '登録中...' : '登録'}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-steam-iron-200">
        すでにアカウントをお持ちですか？{' '}
        <a href="/login" className="text-steam-gold-400 underline">ログイン</a>
      </p>
    </main>
  );
}
```

### 修正2: login ページ更新

**ファイル**: `toybox-app/frontend/src/app/login/page.tsx`

```tsx
'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { getAnonId, setAnonId, generateAnonId } from '../../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'email' | 'anon'>('email');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [anonId, setId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onEmailLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || 'Login failed');
      }

      // ログイン成功 → マイページへ
      router.push('/mypage');
    } catch (err: any) {
      setError(err.message || 'ログインに失敗しました');
    } finally {
      setLoading(false);
    }
  }

  function onAnonLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!anonId) {
      const id = generateAnonId();
      setAnonId(id);
      setId(id);
    } else {
      setAnonId(anonId);
    }
    router.push('/mypage');
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-2xl font-bold text-steam-gold-300">ログイン</h1>
      
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setMode('email')}
          className={`flex-1 rounded px-4 py-2 ${mode === 'email' ? 'bg-steam-gold-500 text-black' : 'bg-steam-iron-800 text-steam-gold-300'}`}
        >
          メール
        </button>
        <button
          onClick={() => setMode('anon')}
          className={`flex-1 rounded px-4 py-2 ${mode === 'anon' ? 'bg-steam-gold-500 text-black' : 'bg-steam-iron-800 text-steam-gold-300'}`}
        >
          匿名
        </button>
      </div>

      {mode === 'email' ? (
        <form onSubmit={onEmailLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-steam-gold-300">メールアドレス</label>
            <input 
              type="email" 
              required 
              className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
            />
          </div>
          <div>
            <label className="block text-sm text-steam-gold-300">パスワード</label>
            <input 
              type="password" 
              required 
              className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
            />
          </div>
          {error && <div className="text-red-400 text-sm">{error}</div>}
          <button 
            disabled={loading} 
            className="rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400 disabled:opacity-50 w-full"
          >
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
          <p className="text-center text-sm text-steam-iron-200">
            アカウントをお持ちでない方は{' '}
            <a href="/signup" className="text-steam-gold-400 underline">新規登録</a>
          </p>
        </form>
      ) : (
        <form onSubmit={onAnonLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-steam-gold-300">匿名ID</label>
            <input 
              className="w-full rounded border border-steam-iron-700 bg-steam-iron-900 p-2" 
              value={anonId || generateAnonId()} 
              onChange={(e) => setId(e.target.value)} 
            />
          </div>
          <button className="rounded bg-steam-gold-500 px-4 py-2 text-black hover:bg-steam-gold-400 w-full">
            匿名で入室
          </button>
        </form>
      )}
    </main>
  );
}
```

### 修正3: トップページにサインアップボタン追加

**ファイル**: `toybox-app/frontend/src/app/page.tsx` (76-82行目を置き換え)

```tsx
{anonId ? (
  <div className="mt-6 flex justify-center gap-3">
    <Link href="/mypage" className="rounded bg-steam-gold-500 px-6 py-3 text-black text-base md:text-lg hover:bg-steam-gold-400">
      マイページへ
    </Link>
  </div>
) : (
  <div className="mt-6 flex justify-center gap-3">
    <Link href="/login" className="rounded bg-steam-gold-500 px-6 py-3 text-black text-base md:text-lg hover:bg-steam-gold-400">
      ログイン
    </Link>
    <Link href="/signup" className="rounded border-2 border-steam-gold-500 px-6 py-3 text-steam-gold-500 text-base md:text-lg hover:bg-steam-gold-500/10">
      アカウント作成（無料）
    </Link>
  </div>
)}
```

---

## 動作確認手順

### 1. バックエンド起動
```bash
cd toybox-app/backend
npm install  # bcrypt, jsonwebtoken, cookie-parser をインストール
npm run dev
```

### 2. フロントエンド起動
```bash
cd toybox-app/frontend
npm run dev
```

### 3. E2Eテスト

#### 提出
1. `/mypage` で画像選択
2. アップロード実行
3. `POST /api/submit/upload` が200を返すことを確認
4. プレビューに画像が表示される
5. リワード（カード/称号/スロット）が表示される

#### プロフィール
1. `/profile` で画像選択（アバター: 2MB以内、ヘッダー: 5MB以内）
2. アップロード成功後、画像が即座に反映される
3. 名前・自己紹介を入力して保存
4. `/profile/view` で更新内容が表示される

#### サインアップ/ログイン
1. `/signup` でメール・パスワード・名前を入力
2. 登録成功 → トップページへリダイレクト
3. `/login` でメール・パスワードでログイン
4. ログイン成功 → マイページへ
5. ヘッダーの「ログアウト」で Cookie が削除される

---

## 環境変数

### フロントエンド (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:4000
```

### バックエンド (`.env`)
```
JWT_SECRET=change_me_strong_secret_in_production
CORS_ORIGINS=http://localhost:3000
MAX_UPLOAD_MB_AVATAR=2
MAX_UPLOAD_MB_HEADER=5
MAX_UPLOAD_MB_POST=10
```

---

## トラブルシューティング

### 画像が反映されない
- ブラウザキャッシュが原因
- `?t=${Date.now()}` をURLに付与してキャッシュ回避

### CORS エラー
- バックエンドの `CORS_ORIGINS` に `http://localhost:3000` が含まれているか確認

### 認証エラー
- Cookie が `httpOnly` + `sameSite: 'lax'` で設定されているか確認
- フロントエンド fetch で `credentials: 'include'` を指定

### アップロード 413/400
- ファイルサイズが上限を超えていないか確認
- 拡張子が jpg/jpeg/png/webp のいずれかか確認

---

## 完了基準

- ✅ 提出アップロード: 画像選択→送信→プレビュー表示
- ✅ プロフィール: 画像/名前/紹介文が保存・即時反映
- ✅ サインアップ: `/signup` で登録→自動ログイン
- ✅ ログイン: `/login` でメール認証＋匿名選択可能
- ✅ ログアウト: Cookie 削除→トップへ

以上の実装で3大不具合がすべて解消されます！

