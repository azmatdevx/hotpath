// Resolve a step's target element from an ordered list of candidate locators, and log which one matched.
//
// usage inside a flow step:   const el = await find(['Refresh orders button',
//                               (p) => p.getByRole('button', { name: 'Refresh orders' }),
//                               (p) => p.getByText('Refresh orders')]);   await el.click();
// The first item is a label for the target (used in logs and failure bundles). Put the most stable locator
// first (role and accessible name, label, visible text, test id); never an id or class that is generated.
//
// Rules:
//  - a candidate counts only if it matches exactly one visible element; two or more is an error ("ambiguous"),
//    because clicking the wrong one would silently change the journey
//  - if the first candidate fails and a later one matches, the run goes on and is recorded as drifted
//  - if none matches, the step fails with every candidate listed
function createFinder(page, usage) {
  return async function find([label, ...candidates], { timeout = 10000, fallbackTimeout = 2000 } = {}) {
    const tried = [];
    for (let i = 0; i < candidates.length; i++) {
      const loc = candidates[i](page);
      const text = candidates[i].toString().replace(/\s+/g, ' ').slice(0, 120);
      try {
        await loc.first().waitFor({ state: 'visible', timeout: i === 0 ? timeout : fallbackTimeout });
      } catch (e) {
        tried.push({ candidate: text, result: 'not found' });
        continue;
      }
      const n = await loc.count();
      if (n > 1) {
        tried.push({ candidate: text, result: `ambiguous (${n} matches)` });
        const err = new Error(`${label}: candidate ${i} matched ${n} elements`);
        err.tried = tried;
        throw err;
      }
      usage.push({ target: label, used: i, of: candidates.length, drifted: i > 0 });
      return loc;
    }
    const err = new Error(`${label}: no candidate matched`);
    err.tried = tried;
    throw err;
  };
}
module.exports = { createFinder };
