#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block shell commands until the agent has restated the goal, target, permission and tool.

hotpath's perf-mode and sweep-mode have a hard rule: before anything contacts the target, the agent writes back the
goal, target, permission, and tool. Instructions alone were not followed reliably when the request already held the
details, and asking for a reply was not reliable either (the agent reported that it had written one when it had only
reasoned about it), so this hook enforces it with a tool call: a Bash call is refused (exit code 2, with a message the
agent sees) until the session holds either an assistant reply that begins with 'Restating:' or a run of restate.py
(next to this file), which takes the four items as arguments and prints them. The command line is the record.

Install it for the sessions that do performance work (project settings, or --settings), not globally:
  {"hooks": {"PreToolUse": [{"matcher": "Bash",
     "hooks": [{"type": "command", "command": "python3 /path/to/require-restating.py"}]}]}}
It only sees Bash. A tool that contacts the target in another way (an MCP browser, for example) needs its own matcher.
It checks that the message exists, not that it is correct; the operator still reads it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MESSAGE = ("Blocked: before running other commands, restate the task by running this one command with your own words "
           "(Goal, Target and whether it is local, test, shared or production, Permission, and Tool and conditions):\n"
           f"python3 {HERE}/restate.py --goal \"...\" --target \"...\" --kind local|test|shared|production "
           "--permission \"...\" --tool \"...\"\n"
           "That is the hard rule in the perf-mode or sweep-mode skill. Then run the blocked command again.")


RESTATE = "restate.py"


def restated(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                m = e.get("message") if isinstance(e, dict) else None
                if not isinstance(m, dict) or m.get("role") != "assistant" or not isinstance(m.get("content"), list):
                    continue
                for c in m["content"]:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "text" and c.get("text", "").lstrip().startswith("Restating:"):
                        return True
                    if c.get("type") == "tool_use" and c.get("name") == "Bash" and RESTATE in str((c.get("input") or {}).get("command", "")):
                        return True
    except OSError:
        return False
    return False


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)                      # not something we understand: do not block
    if event.get("tool_name") != "Bash":
        sys.exit(0)
    if RESTATE in str((event.get("tool_input") or {}).get("command", "")):
        sys.exit(0)                      # the restating command itself is always allowed
    if restated(event.get("transcript_path", "")):
        sys.exit(0)
    print(MESSAGE, file=sys.stderr)
    sys.exit(2)


main()
