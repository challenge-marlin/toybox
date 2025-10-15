export function getAnonId(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem('anonId');
  } catch {
    return null;
  }
}

export function setAnonId(anonId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('anonId', anonId);
}

export function generateAnonId(): string {
  const rand = Math.random().toString(36).slice(2, 8);
  const ts = Date.now().toString(36).slice(-4);
  return `anon-${ts}-${rand}`;
}


