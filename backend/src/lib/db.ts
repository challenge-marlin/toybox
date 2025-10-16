import mongoose from 'mongoose';

let connected = false;
let connecting = false;

export function isMongoReady(): boolean {
  return connected;
}

export async function connectMongo(uri: string, dbName: string): Promise<void> {
  if (connected || connecting) return;
  connecting = true;
  const maxAttempts = 10;
  const baseDelayMs = 500;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await mongoose.connect(uri, { dbName } as any);
      connected = true;
      break;
    } catch (err) {
      const delay = Math.min(10_000, baseDelayMs * Math.pow(2, attempt - 1));
      await new Promise((r) => setTimeout(r, delay));
      if (attempt === maxAttempts) throw err;
    }
  }
  connecting = false;

  const conn = mongoose.connection;
  conn.on('connected', () => { connected = true; });
  conn.on('disconnected', () => { connected = false; });
  conn.on('error', () => { connected = false; });
}

export async function disconnectMongo(): Promise<void> {
  try {
    await mongoose.disconnect();
  } finally {
    connected = false;
  }
}


