#!/usr/bin/env python3
"""Check har_correlate.py on two synthetic HARs of one journey recorded as different users.

usage: python3 selftest.py
The journey has a CSRF token in HTML, a session cookie, a token in a JSON login response, a cart id used in the path
and the body, a username and password, a client timestamp, and values that are the same for both users.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "har_correlate.py")


def entry(method, url, mime="application/json", resp="", headers=None, body=None, body_mime=None, resp_headers=None,
          status=200):
    e = {"startedDateTime": "2026-01-01T00:00:00Z", "time": 10,
         "request": {"method": method, "url": url, "headers": [{"name": k, "value": v} for k, v in (headers or {}).items()]},
         "response": {"status": status, "headers": [{"name": k, "value": v} for k, v in (resp_headers or [])],
                      "content": {"mimeType": mime, "text": resp}}}
    if body is not None:
        e["request"]["postData"] = {"mimeType": body_mime, "text": body}
    return e


def journey(user, csrf, sid, jwt, ts, cart):
    h = "https://shop.example"
    auth = {"Authorization": f"Bearer {jwt}", "Cookie": f"sid={sid}"}
    return {"log": {"entries": [
        entry("GET", h + "/login", "text/html", f'<form><input type="hidden" name="csrf" value="{csrf}"><input name="username"></form>',
              resp_headers=[("Set-Cookie", f"sid={sid}; Path=/; HttpOnly")]),
        entry("POST", h + "/api/login", resp=json.dumps({"data": {"token": jwt}}), headers={"Cookie": f"sid={sid}"},
              body=f"username={user}&password=pw{user}&csrf={csrf}", body_mime="application/x-www-form-urlencoded"),
        entry("GET", h + f"/api/search?q=laptop&ts={ts}", resp='{"items":[1]}', headers=auth),
        entry("GET", h + "/api/cart/new", resp=json.dumps({"id": cart}), headers=auth),
        entry("POST", h + f"/api/cart/{cart}/items", resp="{}", headers=auth, body=json.dumps({"itemId": 42, "cartId": cart}),
              body_mime="application/json"),
        entry("GET", h + "/static/app.js", "application/javascript", "x"),
    ]}}


def main():
    with tempfile.TemporaryDirectory() as d:
        pa, pb, out = (os.path.join(d, n) for n in ("a.har", "b.har", "out.json"))
        json.dump(journey("alice", "csrfAAAA1111", "sidAAAA2222", "jwtAAAA3333", 1700000000123, "cartAAAA9999"), open(pa, "w"))
        json.dump(journey("bobby", "csrfBBBB1111", "sidBBBB2222", "jwtBBBB3333", 1700000999999, "cartBBBB9999"), open(pb, "w"))
        r = subprocess.run([sys.executable, "-I", TOOL, pa, pb, "--json", out], capture_output=True, text=True)
        rows = {x["value"].split("...")[0]: x for x in json.load(open(out))}
        text = r.stdout
        checks = {
            "the run succeeds": r.returncode == 0,
            "CSRF token is a confirmed correlation from the HTML input": rows["csrf"]["kind"] == "correlation" and "input[name=csrf]" in rows["csrf"]["source"]["where"] and rows["csrf"]["confidence"] == "confirmed",
            "the login token is correlated from the JSON path": rows["jwtA"]["kind"] == "correlation" and rows["jwtA"]["source"]["where"] == "JSON $.data.token",
            "the token is used in more than one request": len(rows["jwtA"]["uses"]) >= 2,
            "the cart id is correlated and used in the path and the body": rows["cart"]["kind"] == "correlation" and {u["location"] for u in rows["cart"]["uses"]} >= {"path", "json"},
            "the session cookie is reported as a cookie": rows["sidA"]["kind"] == "cookie",
            "the username and password are parameters": rows["al"]["kind"] == "parameter" and rows["pw"]["kind"] == "parameter",
            "the client timestamp is generated": rows["1700"]["kind"] == "generated" and rows["1700"]["confidence"] == "timestamp",
            "values that are the same for both users are not reported": "laptop" not in text and not any("42" in k for k in rows),
            "values are masked": "csrfAAAA1111" not in text and "jwtAAAA3333" not in text,
        }
        # a HAR with no bodies is refused
        nb = journey("alice", "csrfAAAA1111", "sidAAAA2222", "jwtAAAA3333", 1700000000123, "cartAAAA9999")
        for e in nb["log"]["entries"]:
            e["response"]["content"].pop("text", None)
        pn = os.path.join(d, "nobody.har")
        json.dump(nb, open(pn, "w"))
        refused = subprocess.run([sys.executable, "-I", TOOL, pn, pb], capture_output=True, text=True)
        checks["a HAR without bodies is refused"] = refused.returncode != 0 and "no response bodies" in (refused.stdout + refused.stderr)
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} correlation checks pass")


main()
