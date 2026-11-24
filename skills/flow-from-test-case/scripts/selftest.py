#!/usr/bin/env python3
"""Check cli_to_flow.py build on a hand-made log: stable code translates, risky code is warned about.

usage: python3 selftest.py
It does not run playwright-cli. If node is installed it also checks the generated file parses.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "cli_to_flow.py")

LOG = [
    {"step": "Open the base URL", "kind": "cli", "command": "open http://x.example/start?a=1",
     "code": ["await page.goto('http://x.example/start?a=1');"]},
    {"step": "Click the Save button", "kind": "cli", "command": "click e1",
     "code": ["await page.getByRole('button', { name: 'Save' }).click();"]},
    {"step": "Click the first row", "kind": "cli", "command": "click e2",
     "code": ["await page.getByRole('row').first().click();"]},
    {"step": "Click the generated button", "kind": "cli", "command": "click e3",
     "code": ["await page.locator('#btn-91ac22').click();"]},
    {"step": "Type the password", "kind": "cli", "command": "fill e4 hunter2",
     "code": ["await page.getByLabel('Password').fill('hunter2');"]},
    {"step": "Do something odd", "kind": "cli", "command": "x", "code": ["await page.evaluate(() => 1);"]},
    {"step": "Wait 2 seconds", "kind": "wait-ms", "ms": 2000},
]
TESTCASE = """# TC
## Steps
1. Open the base URL.
2. Click the Save button.
3. Click the first row.
4. Click the generated button.
5. Type the password.
6. Do something odd.
7. Wait 2 seconds.
8. A step that was never recorded.
## Expected result
- x
"""


def main():
    with tempfile.TemporaryDirectory() as d:
        log, tc, out = (os.path.join(d, n) for n in ("log.jsonl", "tc.md", "flow.js"))
        open(log, "w").write("\n".join(json.dumps(e) for e in LOG) + "\n")
        open(tc, "w").write(TESTCASE)
        r = subprocess.run([sys.executable, "-I", TOOL, "build", log, "--id", "t", "--test-case", tc,
                            "--expect-text", "Done", "--out", out], capture_output=True, text=True)
        text, flow = r.stdout, open(out).read()
        checks = {
            "goto becomes base + path": 'page.goto(base + "/start?a=1")' in flow,
            "stable role locator goes through find": "find([\"Click the Save button\", (p) => p.getByRole('button', { name: 'Save' })])" in flow,
            "position-based locator is flagged": "position-based" in text,
            "CSS id locator is flagged": "CSS selector" in text,
            "secret value is replaced": "process.env.SWEEP_SECRET" in flow and "hunter2" not in flow,
            "untranslated code is flagged": "not translated" in text and "NOT TRANSLATED" in flow,
            "unrecorded test case step is flagged": "never recorded" in text,
            "warnings give a non-zero exit": r.returncode == 1,
            "verify waits for the expected text": 'getByText("Done", { exact: true })' in flow,
        }
        # a clean log with matching steps must exit 0 with no warnings
        clean = LOG[:2] + LOG[-1:]
        open(log, "w").write("\n".join(json.dumps(e) for e in clean) + "\n")
        open(tc, "w").write("# TC\n## Steps\n1. Open the base URL.\n2. Click the Save button.\n3. Wait 2 seconds.\n")
        r2 = subprocess.run([sys.executable, "-I", TOOL, "build", log, "--id", "t", "--test-case", tc,
                             "--expect-text", "Done", "--out", out], capture_output=True, text=True)
        checks["a clean log exits 0 with no warnings"] = r2.returncode == 0 and "WARNING" not in r2.stdout
        deep = os.path.join(tmp_deep := os.path.join(d, "no", "such", "dir"), "flow.js")
        r3 = subprocess.run([sys.executable, "-I", TOOL, "build", log, "--id", "t", "--expect-text", "Done", "--out", deep],
                            capture_output=True, text=True)
        checks["the output folder is created when it does not exist"] = os.path.exists(deep) and "Traceback" not in r3.stderr
        if shutil.which("node"):
            checks["generated file parses"] = subprocess.run(["node", "--check", out]).returncode == 0
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} converter checks pass")


main()
