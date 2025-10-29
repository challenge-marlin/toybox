import { test, expect } from '@playwright/test';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || process.env.E2E_API_BASE || 'http://localhost:4000';

test('backend health returns ok', async ({ request }) => {
  const res = await request.get(`${API_BASE}/health`);
  expect(res.ok()).toBeTruthy();
  const json = await res.json();
  expect(json).toMatchObject({ status: 'ok' });
});
