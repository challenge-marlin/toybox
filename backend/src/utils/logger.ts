type LogLevel = 'debug' | 'info' | 'warn' | 'error';

function ts() {
  return new Date().toISOString();
}

function base(level: LogLevel, msg: string, meta?: Record<string, unknown>) {
  const record: Record<string, unknown> = {
    ts: ts(),
    level,
    msg,
    ...(meta || {})
  };
  // Simple structured log as JSON line
  try {
    // eslint-disable-next-line no-console
    console.log(JSON.stringify(record));
  } catch {
    // eslint-disable-next-line no-console
    console.log(`[${record.ts}] ${record.level}: ${record.msg}`);
  }
}

export const logger = {
  debug: (msg: string, meta?: Record<string, unknown>) => base('debug', msg, meta),
  info: (msg: string, meta?: Record<string, unknown>) => base('info', msg, meta),
  warn: (msg: string, meta?: Record<string, unknown>) => base('warn', msg, meta),
  error: (msg: string, meta?: Record<string, unknown>) => base('error', msg, meta)
};
