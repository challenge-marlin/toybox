'use client';
import React from 'react';
import { usePathname } from 'next/navigation';

export default function Footer() {
  const pathname = usePathname();
  if (!pathname || pathname === '/') return null;
  return (
    <footer className="border-t border-steam-iron-800 bg-steam-iron-900/70">
      <div className="mx-auto max-w-6xl p-3 text-center text-sm text-steam-iron-300">
        ©2025 AYATORI.Inc
      </div>
    </footer>
  );
}



