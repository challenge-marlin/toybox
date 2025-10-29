'use client';
import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

export type ToastKind = 'success' | 'error' | 'warning' | 'info';
export type ToastItem = { id: string; kind: ToastKind; message: string; timeoutMs?: number };

type ToastContextType = {
  show: (kind: ToastKind, message: string, opts?: { timeoutMs?: number }) => void;
  success: (message: string, opts?: { timeoutMs?: number }) => void;
  error: (message: string, opts?: { timeoutMs?: number }) => void;
  warning: (message: string, opts?: { timeoutMs?: number }) => void;
  info: (message: string, opts?: { timeoutMs?: number }) => void;
};

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast(): ToastContextType {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
}

export default function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timeoutsRef = useRef<Map<string, any>>(new Map());

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const m = timeoutsRef.current;
    const h = m.get(id); if (h) { try { clearTimeout(h); } catch {} m.delete(id); }
  }, []);

  const show = useCallback((kind: ToastKind, message: string, opts?: { timeoutMs?: number }) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const timeoutMs = opts?.timeoutMs ?? (kind === 'error' ? 6000 : 3500);
    const item: ToastItem = { id, kind, message, timeoutMs };
    setToasts((prev) => [...prev, item].slice(-5));
    const h = setTimeout(() => remove(id), timeoutMs);
    timeoutsRef.current.set(id, h);
  }, [remove]);

  const api = useMemo<ToastContextType>(() => ({
    show,
    success: (m, o) => show('success', m, o),
    error: (m, o) => show('error', m, o),
    warning: (m, o) => show('warning', m, o),
    info: (m, o) => show('info', m, o),
  }), [show]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div aria-live="polite" aria-atomic="true" className="fixed inset-x-0 bottom-3 z-[2000] flex justify-center pointer-events-none">
        <div className="flex flex-col gap-2 w-[92%] max-w-md pointer-events-auto">
          {toasts.map((t) => (
            <div key={t.id} className={[
              'rounded border px-3 py-2 shadow-md text-sm',
              t.kind === 'success' ? 'bg-green-900/70 border-green-500 text-green-100' :
              t.kind === 'error' ? 'bg-red-900/70 border-red-500 text-red-100' :
              t.kind === 'warning' ? 'bg-yellow-900/70 border-yellow-500 text-yellow-100' :
              'bg-steam-iron-900/80 border-steam-iron-700 text-steam-iron-100'
            ].join(' ')} role="status">
              <div className="flex items-start gap-2">
                <span className="mt-0.5">
                  {t.kind === 'success' ? '✅' : t.kind === 'error' ? '⚠️' : t.kind === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <div className="flex-1 whitespace-pre-wrap break-words">{t.message}</div>
                <button onClick={() => remove(t.id)} className="ml-2 text-xs text-steam-iron-200 hover:underline">閉じる</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </ToastContext.Provider>
  );
}
