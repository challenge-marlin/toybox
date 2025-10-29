'use client';
import React, { useEffect } from 'react';
import { onCLS, onLCP, onFID, onINP, Metric } from 'web-vitals';

function send(name: string, value: number) {
  try {
    const base = process.env.NEXT_PUBLIC_API_BASE || '';
    const url = base ? `${base}/api/metrics/webvitals` : '/api/metrics/webvitals';
    navigator.sendBeacon?.(url, new Blob([JSON.stringify({ name, value })], { type: 'application/json' }))
      || fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, value }), keepalive: true });
  } catch {}
}

export default function WebVitalsReporter() {
  useEffect(() => {
    const wrap = (name: string) => (m: Metric) => { if (typeof m.value === 'number') send(name, m.value); };
    try { onCLS(wrap('CLS')); } catch {}
    try { onLCP(wrap('LCP')); } catch {}
    try { onFID(wrap('FID')); } catch {}
    try { onINP(wrap('INP')); } catch {}
  }, []);
  return null;
}
