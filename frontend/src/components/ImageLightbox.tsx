"use client";
import React, { useEffect, useCallback } from 'react';

type Props = {
  src: string;
  alt?: string;
  open: boolean;
  onClose: () => void;
  type?: 'image' | 'video';
};

export default function ImageLightbox({ src, alt, open, onClose, type = 'image' }: Props) {
  const onKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onKeyDown]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center" aria-modal="true" role="dialog">
      {/* background overlay */}
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />

      {/* content */}
      <div className="relative z-[1001] mx-4 max-h-[90dvh]">
        {/* close button */}
        <button
          aria-label="閉じる"
          className="absolute -top-10 right-0 rounded bg-black/60 text-white px-3 py-1 hover:bg-black/80"
          onClick={onClose}
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
      </div>
    </div>
  );
}


