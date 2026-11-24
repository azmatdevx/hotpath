# Claude Code hook: enforce the restating hard rule

The `perf-mode` and `sweep-mode` hard rule says to write the goal, target, permission, and tool back before anything contacts the target. Asking for it in the skill was not reliable: in four test runs the agent skipped it when the request already held the details, and twice it reported having written the restatement when its transcript held only reasoning. So for Claude Code there is a hook that enforces it.

- `require-restating.py` is a `PreToolUse` hook for `Bash`. It refuses a shell command until the session holds a run of `restate.py` (or an assistant reply that begins with `Restating:`), and tells the agent exactly which command to run.
- `restate.py --goal ... --target ... --kind local|test|shared|production --permission ... --tool ...` prints the restatement and refuses if an item is missing. The command line is the record the operator reads; it is also what unlocks the hook.

## Install
Put this in the settings of the sessions that do performance work (project settings, or `--settings`), not in global settings, because it blocks every shell command until the restatement runs:
```json
{"hooks": {"PreToolUse": [{"matcher": "Bash",
  "hooks": [{"type": "command", "command": "python3 /path/to/hotpath/examples/hooks/claude-code/require-restating.py"}]}]}}
```
The allowlist must permit `python3` (it runs `restate.py`).

## What it does not do
- It checks that a restatement was made, not that it is right. The operator still reads it.
- It only sees `Bash`. A tool that reaches the target another way (an MCP browser, for example) needs its own matcher.
- It reads the session transcript, so it needs sessions to be saved (do not start the session with `--no-session-persistence`).
- Other agents have no equivalent here; the rule stays an instruction there.

`python3 selftest.py` checks both scripts.
