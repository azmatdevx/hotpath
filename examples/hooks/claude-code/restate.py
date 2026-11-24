#!/usr/bin/env python3
"""Write down the restatement the hotpath hard rule asks for, as a command, so it is recorded and checkable.

usage: restate.py --goal TEXT --target TEXT --kind local|test|shared|production --permission TEXT --tool TEXT
It prints the restatement and exits 0, or exits 1 naming what is missing. The command line is the record: the operator
sees it in the session, and require-restating.py lets other commands through once it has run.
Do not put secrets in the arguments.
"""
import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--goal", default="")
ap.add_argument("--target", default="")
ap.add_argument("--kind", default="", choices=["", "local", "test", "shared", "production"])
ap.add_argument("--permission", default="")
ap.add_argument("--tool", default="")
a = ap.parse_args()
missing = [n for n in ("goal", "target", "kind", "permission", "tool") if not getattr(a, n).strip()]
if missing:
    sys.exit("restate.py: missing " + ", ".join("--" + m for m in missing) + ". Say what you will do, to what, and why you may.")
print("Restating:")
print(f"- Goal: {a.goal}")
print(f"- Target: {a.target} ({a.kind})")
print(f"- Permission: {a.permission}")
print(f"- Tool and conditions: {a.tool}")
if a.kind == "production":
    print("Note: production is never a target unless the user named it for this task.")
