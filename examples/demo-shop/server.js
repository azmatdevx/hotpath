// Synthetic demo target for hotpath exercises. In-memory, no dependencies.
// Not a real application: it exists so skills can be practiced against a safe local system.
const http = require('http');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 3917);
const DB_SLOTS = Number(process.env.DB_SLOTS || 8);      // the deliberate bottleneck
const DB_MS = Number(process.env.DB_MS || 15);           // time per "query"
const DEGRADE_QUEUE = Number(process.env.DEGRADE_QUEUE || 200); // queue length that triggers degraded search

const sessions = new Map();   // sid -> { csrf, token, user }
const tokens = new Map();     // token -> user
const carts = new Map();      // cartId -> { user, items, used }
let orders = 0;
const rand = () => crypto.randomBytes(12).toString('hex');

// Simulated database: DB_SLOTS concurrent queries, each takes DB_MS, the rest wait in a queue.
let inUse = 0;
const waiting = [];
function query() {
  return new Promise((resolve) => {
    const run = () => { inUse++; setTimeout(() => { inUse--; resolve(); const n = waiting.shift(); if (n) n(); }, DB_MS); };
    inUse < DB_SLOTS ? run() : waiting.push(run);
  });
}
const queries = async (n) => { for (let i = 0; i < n; i++) await query(); };

const parseCookies = (req) => Object.fromEntries((req.headers.cookie || '').split(';').filter(Boolean).map((c) => c.trim().split('=')));
const body = (req) => new Promise((r) => { let b = ''; req.on('data', (d) => (b += d)); req.on('end', () => r(b)); });
const send = (res, code, obj, headers = {}) => {
  const isHtml = typeof obj === 'string';
  res.writeHead(code, { 'Content-Type': isHtml ? 'text/html' : 'application/json', ...headers });
  res.end(isHtml ? obj : JSON.stringify(obj));
};
const authUser = (req) => tokens.get((req.headers.authorization || '').replace('Bearer ', ''));

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  try {
    if (req.method === 'GET' && url.pathname === '/login') {
      const sid = rand(), csrf = rand();
      sessions.set(sid, { csrf });
      return send(res, 200, `<form method="post" action="/login"><input type="hidden" name="csrf" value="${csrf}"><input name="username"><input name="password"></form>`,
        { 'Set-Cookie': `sid=${sid}; Path=/; HttpOnly` });
    }
    if (req.method === 'POST' && url.pathname === '/login') {
      const form = new URLSearchParams(await body(req));
      const s = sessions.get(parseCookies(req).sid);
      if (!s || s.csrf !== form.get('csrf')) return send(res, 403, { error: 'bad csrf' });
      const m = /^user(\d+)$/.exec(form.get('username') || '');
      if (!m || form.get('password') !== `pass-${m[1]}`) return send(res, 401, { error: 'bad credentials' });
      await queries(1);
      const token = rand(); tokens.set(token, form.get('username'));
      return send(res, 200, { token });
    }
    if (req.method === 'GET' && url.pathname === '/metrics') return send(res, 200, { dbInUse: inUse, dbQueue: waiting.length, orders });
    const user = authUser(req);
    if (!user) return send(res, 401, { error: 'unauthenticated' });

    if (req.method === 'GET' && url.pathname === '/search') {
      if (waiting.length > DEGRADE_QUEUE) return send(res, 200, { items: [] }); // degraded: 200 but no work done
      await queries(2);
      const q = url.searchParams.get('q') || '';
      return send(res, 200, { items: Array.from({ length: 5 }, (_, i) => ({ id: `${q}-${i}`, name: `${q} item ${i}`, price: 10 + i })) });
    }
    if (req.method === 'POST' && url.pathname === '/cart') {
      const b = JSON.parse((await body(req)) || '{}');
      if (!b.itemId) return send(res, 400, { error: 'itemId required' });
      await queries(1);
      const cartId = rand(); carts.set(cartId, { user, items: [b.itemId], used: false });
      return send(res, 200, { cartId });
    }
    if (req.method === 'POST' && url.pathname === '/checkout') {
      const b = JSON.parse((await body(req)) || '{}');
      const cart = carts.get(b.cartId);
      if (!cart || cart.user !== user) return send(res, 404, { error: 'cart not found' });
      if (cart.used) return send(res, 409, { error: 'cart already checked out' });
      cart.used = true;
      await queries(4);
      orders++;
      return send(res, 200, { orderId: `ORD-${rand().slice(0, 8)}`, status: 'confirmed' });
    }
    send(res, 404, { error: 'not found' });
  } catch (e) { send(res, 500, { error: String(e) }); }
}).listen(PORT, () => console.log(`demo-shop on :${PORT} (db slots ${DB_SLOTS}, ${DB_MS} ms/query)`));
