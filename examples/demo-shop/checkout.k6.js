// Journey: login (CSRF + session cookie) -> search -> add to cart -> checkout.
// Run:  k6 run -e SCENARIO=smoke checkout.k6.js
// Scenarios: smoke (1 user, 1 iteration), concurrent (5 users x 3), steps (20/40/60/80), knee (60/65/70/75), hold (RATE for HOLD), load (constant arrival rate)
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { parseHTML } from 'k6/html';
import exec from 'k6/execution';

const BASE = __ENV.BASE_URL || 'http://localhost:3917';
const USERS = Number(__ENV.USERS || 1000);       // synthetic users user1..userN
const THINK = Number(__ENV.THINK_SCALE || 1);    // scales think time
const SCENARIO = __ENV.SCENARIO || 'smoke';

const scenarios = {
  smoke: { executor: 'shared-iterations', vus: 1, iterations: 1 },
  concurrent: { executor: 'per-vu-iterations', vus: 5, iterations: 3 },
  steps: {   // 20 -> 40 -> 60 -> 80 iterations/s; 5-10 s ramp then 50 s hold per step (225 s total)
    executor: 'ramping-arrival-rate', startRate: 1, timeUnit: '1s',
    preAllocatedVUs: Number(__ENV.PREALLOC || 100), maxVUs: 1500,
    stages: [
      { target: 20, duration: '10s' }, { target: 20, duration: '50s' },
      { target: 40, duration: '5s' }, { target: 40, duration: '50s' },
      { target: 60, duration: '5s' }, { target: 60, duration: '50s' },
      { target: 80, duration: '5s' }, { target: 80, duration: '50s' },
    ],
  },
  knee: {    // 60 -> 65 -> 70 -> 75 iterations/s; same timing as 'steps' (225 s total)
    executor: 'ramping-arrival-rate', startRate: 1, timeUnit: '1s',
    preAllocatedVUs: Number(__ENV.PREALLOC || 100), maxVUs: 1500,
    stages: [
      { target: 60, duration: '10s' }, { target: 60, duration: '50s' },
      { target: 65, duration: '5s' }, { target: 65, duration: '50s' },
      { target: 70, duration: '5s' }, { target: 70, duration: '50s' },
      { target: 75, duration: '5s' }, { target: 75, duration: '50s' },
    ],
  },
  hold: {    // ramp to RATE over 30 s, then hold it for HOLD (default 5m): does the queue settle?
    executor: 'ramping-arrival-rate', startRate: 1, timeUnit: '1s',
    preAllocatedVUs: Number(__ENV.PREALLOC || 100), maxVUs: 1500,
    stages: [
      { target: Number(__ENV.RATE || 62), duration: '30s' },
      { target: Number(__ENV.RATE || 62), duration: __ENV.HOLD || '5m' },
    ],
  },
  load: {
    executor: 'constant-arrival-rate',
    rate: Number(__ENV.RATE || 20), timeUnit: '1s', duration: __ENV.DURATION || '2m',
    preAllocatedVUs: 50, maxVUs: 500,
  },
};

export const options = {
  scenarios: { [SCENARIO]: scenarios[SCENARIO] },
  thresholds: {
    checks: ['rate>0.99'],
    http_req_failed: ['rate<0.01'],
  },
};

const think = () => sleep(THINK * (0.5 + Math.random()));
const json = { 'Content-Type': 'application/json' };

export default function () {
  const n = (exec.scenario.iterationInTest % USERS) + 1;   // unique user per iteration until the pool wraps
  let token;
  let cartId;

  group('01_login', () => {
    const page = http.get(`${BASE}/login`, { tags: { name: '01a_login_page' } });
    const csrf = parseHTML(page.body).find('input[name=csrf]').attr('value');
    if (!check(csrf, { 'csrf extracted': (v) => !!v })) return;
    const res = http.post(`${BASE}/login`,
      { csrf, username: `user${n}`, password: `pass-${n}` },
      { tags: { name: '01b_login' } });
    token = res.status === 200 ? res.json('token') : undefined;
    check(token, { 'token extracted': (v) => !!v });
  });
  if (!token) return;
  const auth = { Authorization: `Bearer ${token}` };
  think();

  group('02_search', () => {
    const res = http.get(`${BASE}/search?q=laptop`, { headers: auth, tags: { name: '02_search' } });
    check(res, {
      'search 200': (r) => r.status === 200,
      'search has items': (r) => r.status === 200 && r.json('items').length > 0,
    });
  });
  think();

  group('03_cart', () => {
    const res = http.post(`${BASE}/cart`, JSON.stringify({ itemId: 'laptop-0' }),
      { headers: { ...auth, ...json }, tags: { name: '03_cart' } });
    cartId = res.status === 200 ? res.json('cartId') : undefined;
    check(cartId, { 'cartId extracted': (v) => !!v });
  });
  if (!cartId) return;
  think();

  group('04_checkout', () => {
    const res = http.post(`${BASE}/checkout`, JSON.stringify({ cartId }),
      { headers: { ...auth, ...json }, tags: { name: '04_checkout' } });
    check(res, {
      'checkout 200': (r) => r.status === 200,
      'order confirmed': (r) => r.status === 200 && r.json('status') === 'confirmed' && r.json('orderId').startsWith('ORD-'),
    });
  });
}
