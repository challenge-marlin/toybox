import './globals.css';
import React from 'react';
import HeaderNav from '../components/HeaderNav';

export const metadata = {
  title: 'ToyBox',
  description: 'ToyBox Frontend',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <HeaderNav />
        {children}
      </body>
    </html>
  );
}
