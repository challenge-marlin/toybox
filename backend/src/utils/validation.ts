export type ValidationError = { field: string; message: string };

export function requireString(value: any, field: string, opts?: { max?: number }) {
  if (typeof value !== 'string' || value.length === 0) {
    throw { field, message: `${field} is required` } as ValidationError;
  }
  if (opts?.max && value.length > opts.max) {
    throw { field, message: `${field} must be <= ${opts.max} chars` } as ValidationError;
  }
}

export function requireStringArrayLen(value: any, field: string, len: number) {
  if (!Array.isArray(value) || value.length !== len || value.some((v) => typeof v !== 'string')) {
    throw { field, message: `${field} must be string[${len}]` } as ValidationError;
  }
}

export function pickValidationErrors(err: any): ValidationError[] {
  if (!err) return [];
  if (Array.isArray(err)) return err as ValidationError[];
  if (err.field && err.message) return [err as ValidationError];
  return [{ field: 'unknown', message: String(err?.message || err) }];
}
