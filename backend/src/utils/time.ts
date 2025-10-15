// JST (Asia/Tokyo) utilities

const JST_OFFSET_MINUTES = 9 * 60; // UTC+9

export function toJstDate(d: Date | number | string): Date {
  const base = d instanceof Date ? d : new Date(d);
  // Create a new Date representing the same wall-clock time in JST
  const utc = Date.UTC(
    base.getUTCFullYear(),
    base.getUTCMonth(),
    base.getUTCDate(),
    base.getUTCHours(),
    base.getUTCMinutes(),
    base.getUTCSeconds(),
    base.getUTCMilliseconds()
  );
  return new Date(utc + JST_OFFSET_MINUTES * 60 * 1000);
}

export function startOfJstDay(d: Date | number | string): Date {
  const j = toJstDate(d);
  j.setHours(0, 0, 0, 0);
  // Convert back to UTC timeline
  const utcMs = j.getTime() - JST_OFFSET_MINUTES * 60 * 1000;
  return new Date(utcMs);
}

export function endOfJstDay(d: Date | number | string): Date {
  const j = toJstDate(d);
  j.setHours(23, 59, 59, 999);
  const utcMs = j.getTime() - JST_OFFSET_MINUTES * 60 * 1000;
  return new Date(utcMs);
}


