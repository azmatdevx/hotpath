---
name: script-correlation
description: Use when a load test script fails on replay because of dynamic server values (session IDs, CSRF/auth tokens, ViewState, nonces, timestamps, generated IDs). Finds the dynamic values, extracts them from responses, and substitutes them into later requests, in any tool (JMeter, k6, Locust, Gatling, etc.).
---

# Script correlation

Goal: make a script reuse the values the server generates at runtime instead of the stale values captured during recording.

This skill is tool-agnostic. The method is the same everywhere; only the extraction syntax differs. Per-tool syntax is in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

`<skill-dir>` is the folder containing this SKILL.md; the script is in its `scripts/` folder.

## When to use

- Replay returns 401/403, a redirect to login, or "session expired".
- Replay returns 200 but the page or payload is wrong (an error body, an empty result, a login form).
- Requests carry opaque tokens, hidden form fields, or IDs that change between runs.

## Steps

### 1. Capture twice
Record or run the flow two times, as two different users or sessions if possible. Save both as HAR files or request/response logs, with request and response headers and bodies. Treat these files as secrets: they hold real tokens and cookies. (With `journey-capture`, record bodies and use a different test account for each recording.) A response-only capture shows where values come from but not where they are used, so you cannot tell which later requests carry them.

### 2. Diff to find dynamic values
For HAR files, let the script find the candidates instead of reading the captures yourself (this also keeps the bodies out of your context):

```
python3 <skill-dir>/scripts/har_correlate.py user-a.har user-b.har --json candidates.json
```
It aligns the two recordings request by request, lists every value that differs, and says which are correlations (the value first appears in an earlier response, in both recordings, with the place to extract it), which are cookies, parameters (test data), or client-generated values. Values are masked in its output. It needs response bodies in both files and the same sequence of requests. Check each candidate; it does not decide for you. Without HAR files, compare the captures request by request. Anything that differs and is not user-supplied input is a candidate:

- Cookies and `Set-Cookie` values
- Hidden form fields (CSRF tokens, ViewState, event validation)
- Query and path parameters (IDs, cursors, nonces)
- JSON/XML request body fields
- Headers (`Authorization`, `X-CSRF-Token`, `X-Request-Id`)

Ignore values that vary but are not validated by the server (timestamps used only for logging, random trace IDs). Correlate them only if replay fails without it.

### 3. Find the source of each value
For each dynamic value, search earlier responses (body and headers) for where it first appears. That response is where you extract it. Note:

- the **request** that produces it
- its **location** (header, cookie, JSON path, HTML attribute, regex-able text)
- its **scope** (per session, per page, per iteration, one-time use)

### 4. Extract
Prefer structured extraction over regex, in this order:

1. JSON path or XPath, for JSON/XML bodies
2. CSS selector, for HTML attributes and hidden fields
3. Header or cookie accessor
4. Regex or boundary match, only when none of the above fits

Anchor on stable context (the field name, the attribute) and not on position or length. Make extraction fail loudly if the value is missing: assert it is non-empty right after extracting.

### 5. Substitute
Use the extracted variable in every later request that carried the old value: URL, query, headers, body, and cookies. Check the whole flow, because the same token often appears in several places.

### 6. Verify the correlation worked
A passing status code is not proof. For each correlated flow:

- Assert on **content** of the response that depends on the value (a username, an order number, a known element), not only status.
- Run with **two or more concurrent users** and confirm they do not share values.
- Run the flow **twice in a row** per user to catch values that were only valid for the first iteration.
- Confirm the extracted value changes between iterations where it should.

### 7. Handle special cases
- **Multiple matches:** choose the right one deliberately (first, nth, or a stricter anchor). Never pick "random" by accident.
- **Value used once:** extract fresh before every use.
- **Value in a redirect chain:** extract from the `Location` header or follow the redirects manually.
- **Client-computed values** (signatures, hashes, encrypted payloads, tokens produced by JavaScript): extraction is not enough. Reproduce the computation in the script, or call the same endpoint the JavaScript calls.
- **Auth flows (OAuth/OIDC/SAML):** correlate `state`, `nonce`, `code`, and the resulting token across redirects.

## Pitfalls to avoid
- Hard-coding a captured token and "fixing" the failure by re-recording.
- Checking only the HTTP status after correlating.
- Correlating on a regex that also matches unrelated text.
- Sharing one extracted variable across virtual users.
- Correlating values that don't need it, which adds noise and brittleness.
- Leaving real tokens or credentials committed in scripts or HAR files.

## Done when
- The script passes a single-user run and a multi-user concurrent run with content assertions.
- Every dynamic value is extracted from the response that produces it, and none is hard-coded.
- Extraction fails visibly if the expected value is missing.
- Captured HAR files with real tokens are not committed.
