// Flow for journeys/03-promo-page.md. The page has planted web vitals problems (see server.js).
module.exports = {
  id: 'tc-03-promo-page',
  steps: [
    ['Open the promo page', async (page, base) => { await page.goto(base + '/promo'); }],
    ['Wait for the hero image to load', async (page) => {
      await page.waitForFunction(() => { const i = document.querySelector('img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
    }],
    ['Click "Apply filter"', async (page, base, find) => {
      const button = await find(['Apply filter button', (p) => p.getByRole('button', { name: 'Apply filter' })]);
      await button.click();
    }],
    ['Wait for the filter to apply', async (page) => { await page.getByText('Filter applied', { exact: true }).waitFor({ timeout: 5000 }); }],
  ],
  async verify(page) {
    if ((await page.locator('#status').textContent()) !== 'Filter applied') throw new Error('filter not applied');
  },
};
