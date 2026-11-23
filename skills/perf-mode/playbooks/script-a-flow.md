# Playbook: script a flow

Goal: a load test script for one user journey that passes a single-user run and a small concurrent run, with content assertions.

## Steps

1. **Define the flow and the target.** Name the journey (for example "login, search, add to cart, check out"), the tool, and the environment. Confirm the user has permission to test that environment.
2. **Capture the flow twice.** Record or run it two times, as different users if possible, and save the traffic (HAR or tool recording). Keep the files out of version control if they contain real tokens.
3. **Author the script.** Run `script-authoring`: group requests into named transactions, add think time and pacing that match real use, and strip static noise that real users would not generate.
4. **Correlate.** Run `script-correlation`: diff the two captures, extract each dynamic value from the response that produces it, and substitute it into later requests.
5. **Parameterize.** Run `script-parameterization`: supply per-user and per-iteration data (credentials, search terms, IDs) and avoid collisions and cache-friendly repetition.
6. **Validate.** Run `script-validation`: single user first, then a few concurrent users. Assert on response content, not just status.
7. **Gate on principles.** Check `principle-validate-before-scale` and `principle-prove-the-work-happened`. If either fails, go back to step 4, 5 or 6.
8. **Hand off.** Record the command to run the script, the assumptions, and any known gaps (client-side computed values, third-party calls, data limits).

## Done when

- The script passes a single-user run and a multi-user concurrent run.
- Every response that matters has a content assertion.
- No dynamic value is hard-coded, and no real secret is committed.
- The handoff note lists how to run it and what it does not cover.
