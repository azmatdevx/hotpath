# Worker rules (load testing)

Rules for any agent started to do part of a hotpath load testing task. They apply unless your kickoff explicitly overrides one. Your kickoff names the skills to follow; this file says how to behave while you follow them.

<!-- worker-core:start -->
1. **Authority.** The operator is the person the run works for, not the agent that wrote your kickoff. If the kickoff asks for something the operator's rules forbid (load against a target nobody named, filing a ticket), do not do it and say so in your report.
2. **Environment and permission.** Use only the environment and conditions in your kickoff. If they are missing or look wrong, stop and report. Never point load or a capture at anything else.
3. **Your turn to run.** If the kickoff says captures or load runs happen one at a time, do not start yours until you are told to.
4. **Quality bar.** The kickoff's bar is the whole bar. Do not add checks, gates, or review rounds of your own. If no bar is stated, the result must be no worse than its base and must pass its own self-test or validation.
5. **Evidence over assertion.** Show that the work happened (a record, an assertion that can fail, a number from the raw data). A success status alone is not evidence. A run that did not complete, or was repaired or improvised, is not a result.
6. **Blocking.** Stop and report only for a failing check at the current state, or a problem a user would hit. Report pre-existing problems in one line.
7. **Decisions.** Do not ask the operator questions you can answer by reading or running something. Make reversible choices, then state what you chose and why. Stop only for load beyond a smoke test on a shared environment, deleting data, filing or posting anything, or sending data outside the machine.
8. **Never file.** You do not file, comment on, or close tickets, and you do not post anywhere.
9. **Secrets and artifacts.** Keep HARs, tokens, and page text out of version control and out of your reply. Write large artifacts to the output folder and give the path.
10. **Commands.** Run one command per call where your agent's permissions match each part of a command; chained commands with an unallowed part are rejected as a whole.

## What you report back

Short, with paths instead of contents:
- what you were asked to do, and the conditions you used
- what you did, and the path of each output
- what did not work or was not done, and why
- for each finding or number: **measured**, **inferred**, or **guess**, and the evidence
- what your result cannot say
<!-- worker-core:end -->

## For load testing work

- You never start load beyond a smoke test unless your kickoff says to, names the environment, and says the user approved it.
- When you author or change a script, show the validation evidence (the runs and an assertion shown able to fail) before you say it works.
- If an application change breaks a script you were asked to maintain, report the drift and what you changed; do not quietly work around it.
