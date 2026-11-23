# demo-shop

A synthetic, in-memory target for practicing hotpath skills locally. Not a real application.

```sh
node server.js          # listens on :3917
PORT=4000 DB_SLOTS=4 node server.js
```

Flow: `GET /login` (HTML with hidden `csrf` field, sets `sid` cookie), `POST /login` (form: csrf, username, password; returns bearer token),
`GET /search?q=`, `POST /cart` (returns single-use `cartId`), `POST /checkout` (returns `orderId`).
Users: `user1`, `user2`, ... with password `pass-<n>` (synthetic).

Built-in behaviors for exercises: a limited "database" (`DB_SLOTS`, `DB_MS`) that queues under load, and a degraded `/search` that returns 200 with empty results when the queue is long.
`GET /metrics` shows database slots in use and queue length.

## Exercise files

- `checkout.k6.js`: the journey with correlation, content checks, and `smoke`, `concurrent`, `steps`, and `load` scenarios (`k6 run -e SCENARIO=steps checkout.k6.js`).
- `sample-metrics.py`: samples `/metrics` once per second into a CSV (server-side evidence).
- `analyze.py`: per-step, per-transaction percentiles and server-side figures from k6 CSV output (`k6 run --out csv=raw.csv ...`), standard library only.

Run the target and the generator on separate machines when you can. On one machine they compete for CPU.
