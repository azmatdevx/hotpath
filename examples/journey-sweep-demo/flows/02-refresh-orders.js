// Flow for journeys/02-refresh-orders.md. The button has a generated id, so the target is found by its
// role and visible name, with a text match as a fallback.
module.exports = {
  id: 'tc-02-refresh-orders',
  steps: [
    ['Open the base URL', async (page, base) => { await page.goto(base + '/start'); }],
    ['Wait for the orders count', async (page) => { await page.getByText('3 orders').waitFor({ timeout: 15000 }); }],
    ['Click "Refresh orders"', async (page, base, find) => {
      const button = await find(['Refresh orders button',
        (p) => p.getByRole('button', { name: 'Refresh orders' }),
        (p) => p.getByText('Refresh orders', { exact: true })]);
      await button.click();
    }],
    ['Wait for the refresh to finish', async (page) => { await page.getByText('3 orders (refreshed)').waitFor({ timeout: 15000 }); }],
  ],
  async verify(page) {
    const text = await page.locator('#orders').textContent();
    if (text !== '3 orders (refreshed)') throw new Error('expected "3 orders (refreshed)", got ' + JSON.stringify(text));
  },
};
