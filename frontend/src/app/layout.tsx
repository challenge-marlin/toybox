import './globals.css';
import React from 'react';
import HeaderNav from '../components/HeaderNav';
import ToastProvider from '../components/ToastProvider';
import WebVitalsReporter from '../components/WebVitalsReporter';

export const metadata = {
  title: 'ToyBox',
  description: 'ToyBox Frontend',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <ToastProvider>
          <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[3000] focus:rounded focus:bg-yellow-300 focus:text-black focus:px-3 focus:py-1">本文へスキップ</a>
          <HeaderNav />
          <div id="main-content" tabIndex={-1}></div>
          {children}
          <WebVitalsReporter />
        </ToastProvider>
      </body>
    </html>
  );
}
