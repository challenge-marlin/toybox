"use client";
import React, { useEffect, useCallback, useRef } from 'react';
import { ShareToDiscordButton } from './ShareToDiscordButton';

type Props = {
  src: string;
  alt?: string;
  open: boolean;
  onClose: () => void;
  type?: 'image' | 'video';
  // Optional extra fields to support share caption
  asset?: {
    id: string;
    type: 'image' | 'video' | 'game' | 'other';
    title?: string;
    authorName?: string;
    mimeType: string;
    sizeBytes?: number;
    fileUrl: string;
  };
};

export default function ImageLightbox({ src, alt, open, onClose, type = 'image', asset }: Props) {
  const onKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  const dialogRef = useRef<HTMLDivElement | null>(null);
  const closeBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!open) return;
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onKeyDown]);

  useEffect(() => {
    if (!open) return;
    // 初期フォーカスを閉じるボタンへ
    try { closeBtnRef.current?.focus(); } catch {}
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKeyDownTrap(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;
      const root = dialogRef.current;
      if (!root) return;
      const focusables = root.querySelectorAll<HTMLElement>('button, [href], video[controls], [tabindex]:not([tabindex="-1"])');
      const list = Array.from(focusables).filter((el) => !el.hasAttribute('disabled'));
      if (list.length === 0) return;
      const first = list[0];
      const last = list[list.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey) {
        if (active === first) { e.preventDefault(); last.focus(); }
      } else {
        if (active === last) { e.preventDefault(); first.focus(); }
      }
    }
    window.addEventListener('keydown', onKeyDownTrap);
    return () => window.removeEventListener('keydown', onKeyDownTrap);
  }, [open]);

  if (!open) return null;

  return (
    <div ref={dialogRef} className="fixed inset-0 z-[1000] flex items-center justify-center" aria-modal="true" role="dialog" aria-label={alt || (type === 'video' ? '動画ビューア' : '画像ビューア')}>
      {/* background overlay */}
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />

      {/* content */}
      <div className="relative z-[1001] mx-4 max-h-[90dvh]">
        {/* close button */}
        <button
          aria-label="閉じる"
          className="absolute -top-10 right-0 rounded bg-black/60 text-white px-3 py-1 hover:bg-black/80"
          onClick={onClose}
          ref={closeBtnRef}
        >
          ×
        </button>
        {type === 'video' ? (
          <video
            src={src}
            controls
            className="max-h-[90dvh] max-w-[90vw] shadow-2xl bg-black"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <img
            src={src}
            alt={alt || ''}
            className="max-h-[90dvh] max-w-[90vw] object-contain shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        )}
        {/* actions overlay */}
        {asset && (asset.type === 'image' || asset.type === 'video') ? (
          <div className="absolute top-2 right-2 z-[1002]">
            <ShareToDiscordButton asset={asset} />
          </div>
        ) : null}
      </div>
    </div>
  );
}


