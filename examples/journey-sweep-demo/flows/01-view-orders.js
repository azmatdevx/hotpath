// Flow for journeys/01-view-orders.md. Each step is named so the capture can report how far it got.
module.exports = {
  id: 'tc-01-view-orders',
  steps: [
    ['Open the base URL', async (page, base) => { await page.goto(base + '/start'); }],
    ['Wait for the orders count', async (page) => { await page.getByText('3 orders').waitFor({ timeout: 15000 }); }],
    ['Wait 6 seconds for background activity', async (page) => { await page.waitForTimeout(6000); }],
  ],
  // The end state that proves the journey completed. The capture fails the run if this does not hold.
  async verify(page) {
    const text = await page.locator('#orders').textContent();
    if (text !== '3 orders') throw new Error('expected "3 orders", got ' + JSON.stringify(text));
  },
};
