// Synthetic web app with planted performance problems, to try the journey-sweep skills on.
// Run: node server.js   (port 3918, override with PORT)
// The Refresh orders button gets a new random id and class on every page load.
// Planted: concurrent duplicate calls, a slow API, a huge uncompressed JSON list, an uncompressed and
// uncacheable script, a large image, N+1 item calls, a failing call, a redirect chain, polling.
// Control: a small fingerprinted script, gzip-compressed, served with long-lived cache headers (must not be flagged).
const http = require('http');
const zlib = require('zlib');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 3918);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const bigJson = JSON.stringify(Array.from({ length: 6000 }, (_, i) => ({
  id: i, sku: 'SKU-' + i, name: 'Product ' + i, description: 'x'.repeat(120), tags: ['a', 'b', 'c'],
})));
const vendorJs = '/*' + crypto.randomBytes(300000).toString('base64') + '*/\nwindow.vendorLoaded = true;\n';
const heroPng = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), crypto.randomBytes(900000)]);
const appJs = `
const j = (u) => fetch(u).then((r) => r.json());
async function main() {
  await Promise.all([j('/api/profile'), j('/api/profile'), j('/api/profile')]);  // three components, same data
  const orders = await j('/api/orders');                                         // slow
  document.getElementById('orders').textContent = orders.length + ' orders';
  j('/api/catalog');                                                             // huge
  j('/api/recommendations');                                                     // fails
  for (let i = 1; i <= 8; i++) j('/api/items/' + i);                             // N+1
  setInterval(() => j('/api/notifications'), 1500);                              // polling
  document.body.dataset.ready = '1';
}
main();
async function refreshOrders() {
  await j('/api/orders');
  document.getElementById('orders').textContent = '3 orders (refreshed)';
}
`;
// The button's id and class change on every page load, as in apps with generated ids.
const page = () => {
  const r = crypto.randomBytes(4).toString('hex');
  return `<!doctype html><html><head><title>Shop</title>
<script src="/static/vendor.js"></script><script src="/static/app.3f9c1a.js" defer></script></head>
<body><h1>Orders</h1><img src="/img/hero.png" width="200" alt=""><p id="orders">loading</p>
<button id="btn-${r}" class="c-${r}" onclick="refreshOrders()">Refresh orders</button></body></html>`;
};

function send(res, status, type, body, headers = {}) {
  res.writeHead(status, { 'content-type': type, ...headers });
  res.end(body);
}

http.createServer(async (req, res) => {
  const path = req.url.split('?')[0];
  const gz = /gzip/.test(req.headers['accept-encoding'] || '');
  if (path === '/') return send(res, 200, 'text/html', page(), { 'cache-control': 'no-cache' });
  if (path === '/start') return send(res, 302, 'text/html', '', { location: '/home' });
  if (path === '/home') return send(res, 302, 'text/html', '', { location: '/' });
  if (path === '/static/app.3f9c1a.js')
    return send(res, 200, 'application/javascript', gz ? zlib.gzipSync(appJs) : appJs,
      { 'cache-control': 'public, max-age=31536000, immutable', ...(gz && { 'content-encoding': 'gzip' }) });
  if (path === '/static/vendor.js') return send(res, 200, 'application/javascript', vendorJs);
  if (path === '/img/hero.png') return send(res, 200, 'image/png', heroPng, { 'cache-control': 'public, max-age=86400' });
  if (path === '/api/profile') { await sleep(40); return send(res, 200, 'application/json', '{"name":"Test User"}'); }
  if (path === '/api/orders') { await sleep(1500); return send(res, 200, 'application/json', '[{"id":1},{"id":2},{"id":3}]'); }
  if (path === '/api/catalog') return send(res, 200, 'application/json', bigJson);
  if (path === '/api/recommendations') return send(res, 500, 'application/json', '{"error":"upstream"}');
  if (path === '/api/notifications') return send(res, 200, 'application/json', '[]');
  if (path.startsWith('/api/items/')) { await sleep(60); return send(res, 200, 'application/json', '{"ok":true}'); }
  send(res, 404, 'text/plain', 'not found');
}).listen(PORT, () => console.log('journey-sweep demo on :' + PORT));
