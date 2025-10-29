import { test, expect } from '@playwright/test';

test.describe('Feed page', () => {
  test('loads and shows heading', async ({ page }) => {
    await page.goto('/feed');
    await expect(page.getByRole('heading', { name: 'みんなの投稿' })).toBeVisible();
    // Grid exists
    await expect(page.locator('div.grid')).toBeVisible();
  });
});
