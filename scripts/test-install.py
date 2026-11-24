#!/usr/bin/env python3
"""Check the skills work when installed somewhere else and run from another directory.

Copies skills/ into a temporary '.agents/skills' folder, then from an unrelated working directory:
  - runs each skill's self-test through the copy
  - runs the capture script with no arguments and checks it fails cleanly (exit code 2) instead of crashing on a
    missing file, which is what a broken relative path or a missing package looks like

It does not install a browser or run Playwright. usage: python3 scripts/test-install.py
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
failures = []

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    installed = tmp / "project" / ".agents" / "skills"
    shutil.copytree(ROOT / "skills", installed)
    elsewhere = tmp / "elsewhere"
    elsewhere.mkdir()

    for rel in ("har-analysis/scripts/selftest.py", "flow-from-test-case/scripts/selftest.py",
                "web-vitals-audit/scripts/selftest.py", "script-correlation/scripts/selftest.py",
                "script-authoring/scripts/selftest.py"):
        r = subprocess.run([sys.executable, "-I", str(installed / rel)], cwd=elsewhere, capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"{rel} failed from another directory:\n{r.stdout}{r.stderr}")

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, str(installed / "journey-capture/scripts/capture-playwright.js")], cwd=elsewhere,
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        if r.returncode != 2 or ("playwright package was not found" not in out and "usage:" not in out):
            failures.append(f"capture script did not fail cleanly from another directory (exit {r.returncode}):\n{out[:400]}")
        if "Cannot find module './locate'" in out:
            failures.append("capture script cannot find locate.js next to it")
    else:
        print("node not found: skipped the capture script check")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print("OK: skills run from an installed copy, in another working directory")
