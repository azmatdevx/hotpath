#!/usr/bin/env python3
"""Check summarize_results.py on synthetic k6, JMeter, and generic CSV results with known answers.

usage: python3 selftest.py
Answers are known by construction: label A cycles through 1..100 ms (p50 50.5, p95 95.05), label B is 100 ms in the
first half of the window and 300 ms in the second (drifting), the ramp-up carries 5000 ms outliers that the window
must leave out, and the JMeter and generic files describe the same samples as the k6 file.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summarize_results.py")
K6_HEADER = ["metric_name", "timestamp", "metric_value", "check", "error", "error_code", "expected_response", "group",
             "method", "name", "scenario", "service", "status", "subproto", "tls_version", "url", "extra_tags", "metadata"]
T0, RUN = 1_800_000_000, 400          # the run lasts 400 s; the default window is 60-385 s


def samples():
    """(second, label, elapsed_ms, ok) for 10 samples per second per label."""
    out = []
    for s in range(RUN):
        for i in range(10):
            n = s * 10 + i
            a_ms = 5000 if s < 60 else (n % 100) + 1
            b_ms = 5000 if s < 60 else (100 if s < (60 + 385) / 2 else 300)
            out.append((s, "A", a_ms, not (s >= 60 and n % 20 == 0)))   # 5% of A fails after the ramp
            out.append((s, "B", b_ms, True))
    return out


def run(*args):
    return subprocess.run([sys.executable, "-I", TOOL, *args], capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as d:
        k6, jtl, gen, out = (os.path.join(d, n) for n in ("k6.csv", "jtl.csv", "gen.csv", "out.json"))
        S = samples()
        with open(k6, "w", newline="") as f:
            w = csv.writer(f); w.writerow(K6_HEADER)
            for s, label, ms, ok in S:
                w.writerow(["http_req_duration", T0 + s, ms, "", "", "", "true" if ok else "false", "", "GET", label, "", "",
                            200 if ok else 500, "", "", "", "", ""])
            w.writerow(["checks", T0 + 100, 0, "search has items", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            w.writerow(["checks", T0 + 101, 1, "search has items", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            w.writerow(["dropped_iterations", T0 + 200, 7, "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
        with open(jtl, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["timeStamp", "elapsed", "label", "responseCode", "success"])
            for s, label, ms, ok in S:
                w.writerow([(T0 + s) * 1000, ms, label, 200 if ok else 500, "true" if ok else "false"])
        with open(gen, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["ts", "name", "ms", "status"])
            for s, label, ms, ok in S:
                w.writerow([T0 + s, label, ms, 200 if ok else 500])
        checks = {}
        for name, args in (("k6", [k6]), ("jtl", [jtl]),
                           ("csv", [gen, "--format", "csv", "--col-time", "ts", "--col-label", "name", "--col-elapsed", "ms",
                                    "--col-ok", "status", "--time-unit", "s"])):
            r = run(*args, "--json", out, "--sla", "A=90", "--sla-p95", "250")
            rep = json.load(open(out)) if r.returncode == 0 else {}
            A, B = rep.get("labels", {}).get("A", {}), rep.get("labels", {}).get("B", {})
            checks[f"{name}: runs"] = r.returncode == 0
            checks[f"{name}: A percentiles match the known answer"] = A.get("p50") in (50, 51) and A.get("p95") == 95 and A.get("p99") == 99
            checks[f"{name}: the ramp-up outliers are outside the window"] = A.get("max") == 100 and B.get("max") == 300
            checks[f"{name}: A error rate is 5%"] = A.get("error_pct") == 5.0
            checks[f"{name}: B is flagged as drifting and A is not"] = B.get("drifting") is True and A.get("drifting") is False
            checks[f"{name}: B first and second half p95"] = (B.get("p95_first_half"), B.get("p95_second_half")) == (100, 300)
            checks[f"{name}: limits are applied per label and by default"] = A.get("over_limit") is True and B.get("over_limit") is True and B.get("p95_limit") == 250
            checks[f"{name}: rate is 10 per second"] = A.get("rate_per_s") == 10.0
        rep = json.load(open(out)) if False else None
        r = run(k6, "--json", out)
        rep = json.load(open(out))
        checks["k6: failing checks are reported"] = rep["checks"] == {"search has items": {"evaluated": 2, "failed": 1}}
        checks["k6: dropped iterations are reported"] = rep["dropped_iterations"] == 7 and "Dropped iterations: 7" in r.stdout
        r = run(k6, "--exclude", "^B$", "--json", out)
        checks["--exclude removes a transaction"] = list(json.load(open(out))["labels"]) == ["A"]
        r = run(k6, "--window", "100,150", "--json", out)
        checks["--window sets the window and warns when it is short"] = json.load(open(out))["window"] == [100, 150] and "only 50 s long" in r.stdout
        bad = os.path.join(d, "x.csv"); open(bad, "w").write("a,b\n1,2\n")
        r = run(bad)
        checks["an unrecognised file is refused"] = r.returncode != 0 and "could not recognise" in (r.stdout + r.stderr)
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} results-summary checks pass")


main()
