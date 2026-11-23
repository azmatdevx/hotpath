#!/usr/bin/env python3
"""Sample CPU once per second into a CSV: the generator (k6), the target (node server.js), and the whole machine.

Process CPU is the change in consumed CPU time per wall second, as a percent of one core (so 100 = one core busy).
Machine CPU is the busy share of all cores, from `top` (macOS).
"""
import re, subprocess, sys, time

def pids(args):
    out = subprocess.run(["pgrep"] + args, capture_output=True, text=True).stdout.split()
    return [int(p) for p in out]

def cpu_time(pid_list):
    total = 0.0
    for pid in pid_list:
        t = subprocess.run(["ps", "-o", "time=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
        if not t: continue
        secs = 0.0
        for part in t.split(":"):
            secs = secs * 60 + float(part)
        total += secs
    return total

def machine_busy():
    out = subprocess.run(["top", "-l", "2", "-s", "1", "-n", "0"], capture_output=True, text=True).stdout
    idle = re.findall(r"([\d.]+)% idle", out)
    return 100.0 - float(idle[-1]) if idle else float("nan")

out = sys.argv[1]
prev = {"k6": None, "node": None}
with open(out, "w") as f:
    f.write("ts,k6_cpu_pct,node_cpu_pct,machine_busy_pct\n")
    last = time.time()
    while True:
        busy = machine_busy()            # takes about 1 s, which paces the loop
        now = time.time()
        row = []
        for name, args in (("k6", ["-x", "k6"]), ("node", ["-f", "node server.js"])):
            cur = cpu_time(pids(args))
            row.append(f"{100 * (cur - prev[name]) / (now - last):.0f}" if prev[name] is not None else "")
            prev[name] = cur
        last = now
        f.write(f"{now:.1f},{row[0]},{row[1]},{busy:.0f}\n"); f.flush()
