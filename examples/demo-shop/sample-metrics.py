#!/usr/bin/env python3
"""Sample the demo-shop /metrics endpoint once per second into a CSV (server-side evidence)."""
import json, sys, time, urllib.request

out = sys.argv[1]
base = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3917"
with open(out, "w") as f:
    f.write("ts,dbInUse,dbQueue,orders\n")
    while True:
        try:
            m = json.load(urllib.request.urlopen(f"{base}/metrics", timeout=1))
            f.write(f"{time.time():.1f},{m['dbInUse']},{m['dbQueue']},{m['orders']}\n"); f.flush()
        except Exception:
            pass
        time.sleep(1)
