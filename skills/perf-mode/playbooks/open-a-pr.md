# Playbook: open a PR

You own handing verified work to a reviewer as a pull request that carries its own evidence. Check, branch, commit, push, open. You never merge, and you never push to a shared branch.

Use when: a playbook says to deliver, such as `script-from-test-case` or `repair-a-script`, and its verification gates passed.

## Inputs

- The verified change and the evidence behind it (validation runs, assertions, what changed in the application).
- The repository, its default branch, and its branch and commit conventions.
- Whether a pull request tool is available (for example the `gh` CLI), and whether you are allowed to use it for this task.

## Steps

1. **Check the gates.** The playbook's verification passed and was re-run at this build. If not, go back; do not open a PR to "get review of" unverified work.
2. **Check the diff for what must not be there:** HAR files, captures, tokens, passwords, personal data, local paths, debug listeners, and files you did not mean to change. Remove them.
3. **Branch.** Run git from the repository's own directory (your working directory), not with `git -C` or `cd`: allowlists reject both. Create a new feature branch (for example `perf/<journey>-<change>`) from the default branch. Never commit to the default branch or to a branch someone else owns.
4. **Commit.** One focused commit per logical change, with a message that says what changed and why.
5. **Push the new branch.** Never force-push, and never push to a shared or default branch.
6. **Open the PR as ready for review.** Title `type(scope): subject`. Body of 40 lines or fewer under these headings, dropping empty ones: Why, What changed, Scope, Verification, Not covered, Rollback. Put long evidence (run output, tables) in a file or comment and link it. If you cannot use a PR tool, write the title and body to a file and tell the user.
7. **Report.** Give the PR link, the evidence it carries, and what the reviewer should check first.

## Verification

A pass is a PR whose diff contains only the intended files, whose body states what was verified, against which build and environment, and what was not, and which is not merged. Not a pass: a PR with unverified work, a diff with a capture or a secret, or a branch pushed to a shared name.

## Stop conditions

- A gate failed or the validation was not re-run: stop and fix it.
- The diff contains a secret or a HAR: remove it; if it was already committed, tell the user, because history must be cleaned before pushing.
- You cannot tell which branch is the default or whether you may push to the remote: ask.
- The repository requires a review step or a check you cannot satisfy: say so; do not work around it.

## Delegation

You do this yourself, with the lead's evidence. A worker does not open pull requests.

## Reply format

The PR link, branch, the one-line summary, the verification evidence, what was not covered, and the first thing for the reviewer to check.

## Related playbooks

`script-from-test-case`, `repair-a-script`.

## Done when

- A PR is open for review from a new feature branch, with evidence in the body.
- The diff was checked for captures and secrets.
- Nothing was merged, force-pushed, or pushed to a shared branch.
