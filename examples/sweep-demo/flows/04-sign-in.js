// Flow for journeys/04-sign-in.md. The test user comes from the TEST_USER environment variable, so the same flow
// can be recorded as two different users (see --label in journey-capture).
const user = () => { if (!process.env.TEST_USER) throw new Error('set TEST_USER'); return process.env.TEST_USER; };
module.exports = {
  id: 'tc-04-sign-in',
  steps: [
    ['Open the account page', async (page, base) => { await page.goto(base + '/account'); }],
    ["Type the test user's name", async (page, base, find) => { await (await find(['Username field', (p) => p.getByLabel('Username')])).fill(user()); }],
    ['Click "Sign in"', async (page, base, find) => { await (await find(['Sign in button', (p) => p.getByRole('button', { name: 'Sign in' })])).click(); }],
    ['Wait for the welcome message', async (page) => { await page.getByText('Welcome ' + user(), { exact: true }).waitFor({ timeout: 10000 }); }],
  ],
  async verify(page) {
    const t = await page.locator('#welcome').textContent();
    if (t !== 'Welcome ' + user()) throw new Error('expected a welcome for the test user, got ' + JSON.stringify(t));
  },
};
