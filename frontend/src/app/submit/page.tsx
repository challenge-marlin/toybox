import React from 'react';
import Link from 'next/link';
import SubmitForm from '../../components/SubmitForm';

export default function SubmitPage() {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-steam-gold-300">ToyBox 提出フォーム</h2>
        <Link href="/mypage" className="text-sm text-steam-gold-400 underline">マイページへ</Link>
      </div>
      <p className="mb-6 text-steam-iron-200">1日1回提出できます。提出すると抽選と即時報酬が実行されます。</p>
      <SubmitForm />
    </main>
  );
}



