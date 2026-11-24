#!/usr/bin/env python3
"""Check require-restating.py with synthetic transcripts.

usage: python3 selftest.py
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "require-restating.py")


def run(transcript_lines, tool="Bash"):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.jsonl")
        open(p, "w").write("\n".join(json.dumps(x) for x in transcript_lines) + "\n")
        r = subprocess.run([sys.executable, "-I", HOOK], input=json.dumps({"tool_name": tool, "transcript_path": p}),
                           capture_output=True, text=True)
        return r.returncode, r.stderr


def msg(role, *blocks):
    return {"type": role, "message": {"role": role, "content": list(blocks)}}


def main():
    text = lambda t: {"type": "text", "text": t}
    checks = {}
    code, err = run([msg("user", text("Do the task")), msg("assistant", {"type": "tool_use", "name": "Read", "input": {}})])
    checks["a Bash call with no restating is blocked, with a message"] = code == 2 and "restate.py" in err
    code, _ = run([msg("assistant", text("I'll read the playbook first."))])
    checks["an ordinary message is not a restating"] = code == 2
    code, _ = run([msg("assistant", text("Restating:\n- Goal: x\n- Target: y"))])
    checks["a message that begins with Restating: lets the call through"] = code == 0
    code, _ = run([msg("assistant", text("  \nRestating:\n- Goal: x"))])
    checks["leading whitespace is tolerated"] = code == 0
    code, _ = run([msg("user", text("Restating: my own words"))])
    checks["only an assistant message counts"] = code == 2
    code, _ = run([msg("assistant", text("nothing"))], tool="Read")
    checks["tools other than Bash are not blocked"] = code == 0
    r = subprocess.run([sys.executable, "-I", HOOK], input="not json", capture_output=True, text=True)
    checks["unreadable input does not block"] = r.returncode == 0
    code, _ = run([])
    checks["an empty transcript is blocked"] = code == 2
    code, err = run([msg("assistant", text("hello"))])
    checks["the block message names the restating command"] = "restate.py" in err and "--goal" in err
    code, _ = run([msg("assistant", {"type": "tool_use", "name": "Bash", "input": {"command": "python3 /x/restate.py --goal a"}})])
    checks["a run of restate.py in the session lets later calls through"] = code == 0
    code, _ = run([msg("assistant", {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}})])
    checks["another Bash call does not count as a restating"] = code == 2
    with tempfile.TemporaryDirectory() as d2:
        r = subprocess.run([sys.executable, "-I", HOOK], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "python3 /x/restate.py --goal a"}, "transcript_path": os.path.join(d2, "none.jsonl")}), capture_output=True, text=True)
        checks["the restating command itself is allowed with no transcript"] = r.returncode == 0
    RES = os.path.join(os.path.dirname(HOOK), "restate.py")
    ok = subprocess.run([sys.executable, "-I", RES, "--goal", "g", "--target", "t", "--kind", "local", "--permission", "p", "--tool", "k6"], capture_output=True, text=True)
    checks["restate.py prints a Restating block"] = ok.returncode == 0 and ok.stdout.startswith("Restating:") and "- Target: t (local)" in ok.stdout
    bad_ = subprocess.run([sys.executable, "-I", RES, "--goal", "g"], capture_output=True, text=True)
    checks["restate.py refuses missing items and says which"] = bad_.returncode != 0 and "--target" in bad_.stderr and "--kind" in bad_.stderr
    prod = subprocess.run([sys.executable, "-I", RES, "--goal", "g", "--target", "t", "--kind", "production", "--permission", "p", "--tool", "k"], capture_output=True, text=True)
    checks["restate.py says production is never a default target"] = "never a target unless" in prod.stdout
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} restating-hook checks pass")


main()
