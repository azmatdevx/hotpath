#!/usr/bin/env python3
"""Turn a walk-through with playwright-cli into a flow module for journey-capture. Standard library only.

Record each step as you do it, then build the flow:

  cli_to_flow.py record LOG --step "Open the base URL" -- playwright-cli open http://host/start
  cli_to_flow.py record LOG --step 'Click "Refresh orders"' -- playwright-cli click e4
  cli_to_flow.py record LOG --step "Wait for the orders count" --wait-text "3 orders"
  cli_to_flow.py record LOG --step "Wait 6 seconds" --wait-ms 6000
  cli_to_flow.py build LOG --id tc-02 --test-case journeys/02.md --expect-text "3 orders (refreshed)" --out flows/02.js

`record` runs the command, shows its output, and keeps the Playwright code the CLI printed. `build` writes the flow:
step names are your step text, element actions go through `find` with the printed locator as the first candidate,
and `verify` waits for the expected text. Warnings (exit code 1, file still written) mean it needs review:
  - a locator that is not stable (CSS, id, nth, first/last, a role without a name)
  - code the converter does not know how to translate
  - recorded steps not in the test case, or test case steps never recorded
  - a typed value for a field that looks like a secret (replaced with process.env.SWEEP_SECRET)
The generated flow still has to be proven: run it with journey-capture, and show that verify can fail.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

ACTIONS = r"click|dblclick|fill|check|uncheck|hover|selectOption|type|press|setInputFiles"
SECRET_RE = re.compile(r"pass|secret|token|otp|\bpin\b", re.I)
RECORDABLE = {"open", "goto", "click", "dblclick", "fill", "type", "press", "select", "check", "uncheck", "hover",
              "go-back", "go-forward", "reload"}


def extract_code(output):
    blocks = re.findall(r"```js\n(.*?)```", output, re.S)
    lines = [l.strip() for b in blocks for l in b.splitlines() if l.strip()]
    if not lines:
        lines = [l.strip() for l in output.splitlines() if l.strip().startswith("await page.")]
    return lines


def norm(t):
    return re.sub(r"[\s.:;]+$", "", t.strip().lower())


def record(a, cmd):
    entry = {"step": a.step}
    if a.wait_text is not None:
        entry.update(kind="wait-text", text=a.wait_text)
    elif a.wait_ms is not None:
        entry.update(kind="wait-ms", ms=a.wait_ms)
    else:
        if not cmd:
            sys.exit("give a command after -- or use --wait-text or --wait-ms")
        verb = next((c for c in cmd[1:] if not c.startswith("-")), "")
        if verb not in RECORDABLE:
            sys.exit(f"'{verb}' is not an action to record (snapshot, find, eval and requests only look at the page)")
        out = subprocess.run(cmd, capture_output=True, text=True)
        sys.stdout.write(out.stdout)
        sys.stderr.write(out.stderr)
        if out.returncode:
            sys.exit(out.returncode)
        code = extract_code(out.stdout)
        if not code:
            sys.exit("the command printed no Playwright code; nothing recorded")
        entry.update(kind="cli", command=" ".join(cmd[1:]), code=code)
    with open(a.log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"recorded: {a.step}")


def unstable(loc):
    reasons = []
    if re.search(r"\.(nth|first|last)\(", loc):
        reasons.append("position-based (nth/first/last)")
    m = re.match(r"locator\((['\"])(.*?)\1\)", loc)
    if m:
        reasons.append(f"CSS selector {m.group(2)!r}")
    if re.match(r"getByRole\(\s*'[^']*'\s*\)", loc):
        reasons.append("role with no accessible name")
    return reasons


def translate(line, warnings, step):
    q = json.dumps
    m = re.match(r"await page\.goto\((['\"])(.*?)\1\);?$", line)
    if m:
        from urllib.parse import urlsplit
        u = urlsplit(m.group(2))
        rest = (u.path or "/") + (f"?{u.query}" if u.query else "")
        return f"await page.goto(base + {q(rest)});"
    m = re.match(r"await page\.(keyboard|mouse)\.(.*)$", line)
    if m:
        return line
    m = re.match(r"await page\.(go(Back|Forward)|reload)\(.*\);?$", line)
    if m:
        return line
    # split at the last .action( so nested parentheses in the locator are fine
    hits = list(re.finditer(rf"\.({ACTIONS})\(", line))
    if line.startswith("await page.") and hits:
        h = hits[-1]
        loc = line[len("await page."):h.start()]
        act = h.group(1)
        args = line[h.end():].rstrip(";").rstrip()
        args = args[:-1] if args.endswith(")") else args
        for r in unstable(loc):
            warnings.append(f"step {step!r}: unstable locator, {r}: page.{loc}")
        if act == "fill" and SECRET_RE.search(loc):
            warnings.append(f"step {step!r}: typed value for a secret-looking field replaced with process.env.SWEEP_SECRET")
            args = "process.env.SWEEP_SECRET"
        label = step
        return (f"await (await find([{q(label)}, (p) => p.{loc}])).{act}({args});")
    warnings.append(f"step {step!r}: not translated, add it by hand: {line}")
    return f"// NOT TRANSLATED: {line}"


def build(a):
    entries = [json.loads(l) for l in open(a.log, encoding="utf-8") if l.strip()]
    if not entries:
        sys.exit("the log is empty")
    warnings = []
    steps = []
    q = json.dumps
    for e in entries:
        if e["kind"] == "wait-text":
            body = [f"await page.getByText({q(e['text'])}).waitFor({{ timeout: 15000 }});"]
        elif e["kind"] == "wait-ms":
            body = [f"await page.waitForTimeout({e['ms']});"]
        else:
            body = [translate(l, warnings, e["step"]) for l in e["code"]]
        steps.append((e["step"], body))
    if a.test_case:
        md = open(a.test_case, encoding="utf-8").read()
        sec = md.split("## Steps", 1)[-1].split("\n## ", 1)[0]
        tc = [re.sub(r"^\d+\.\s+", "", l).strip() for l in sec.splitlines() if re.match(r"^\d+\.\s", l.strip())]
        rec = {norm(s) for s, _ in steps}
        for s, _ in steps:
            if norm(s) not in {norm(t) for t in tc}:
                warnings.append(f"recorded step is not in the test case: {s!r}")
        for t in tc:
            if norm(t) not in rec:
                warnings.append(f"test case step was never recorded (not automated?): {t!r}")
    parts = []
    for s, body in steps:
        inner = "\n".join("      " + b for b in body)
        parts.append(f"    [{q(s)}, async (page, base, find) => {{\n{inner}\n    }}],")
    flow = f"""// Generated by cli_to_flow.py from {os.path.basename(a.log)} on {datetime.date.today()}. Review before use.
// Prove it with journey-capture, and show that verify fails when the expected text is wrong.
module.exports = {{
  id: {q(a.id)},
  steps: [
{chr(10).join(parts)}
  ],
  // Throws unless the journey ended in the expected state.
  async verify(page) {{
    await page.getByText({q(a.expect_text)}, {{ exact: true }}).waitFor({{ timeout: 5000 }});
  }},
}};
"""
    open(a.out, "w", encoding="utf-8").write(flow)
    print(f"wrote {a.out} ({len(steps)} steps)")
    for w in warnings:
        print("WARNING:", w)
    sys.exit(1 if warnings else 0)


if __name__ == "__main__":
    argv = sys.argv[1:]
    cmd = []
    if "--" in argv:
        i = argv.index("--")
        argv, cmd = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("record")
    r.add_argument("log")
    r.add_argument("--step", required=True)
    r.add_argument("--wait-text")
    r.add_argument("--wait-ms", type=int)
    b = sub.add_parser("build")
    b.add_argument("log")
    b.add_argument("--id", required=True)
    b.add_argument("--expect-text", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--test-case")
    a = ap.parse_args(argv)
    record(a, cmd) if a.mode == "record" else build(a)
