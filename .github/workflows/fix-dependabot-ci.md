---
description: |
  When pyright, ruff or pytest fails on a Dependabot pull request, Codex fixes the
  code and a new pull request is opened with Dependabot's update and the fix. A
  maintainer approves or closes it. Dependabot's own pull request is left alone and
  closes by itself once the update is on main.

on:
  workflow_run:
    workflows: [pyright, ruff, pytest]
    types: [completed]
    branches: ["dependabot/uv/**"]
    conclusion: failure
  bots: ["dependabot[bot]"]
  # One fix per Dependabot branch, also when the earlier one was closed.
  skip-if-match: "is:pr head:fix/${{ github.event.workflow_run.head_branch }}"
  permissions:
    pull-requests: read # for the search above

# The role check lets people with write access through as well. Only Dependabot's
# own pull requests are fixed.
if: github.event.workflow_run.actor.login == 'dependabot[bot]'

permissions:
  contents: read
  actions: read
  pull-requests: read

# One fix at a time for a branch. The conclusion is part of the group so that a run
# for a check that passed cannot push a waiting fix out of the queue.
concurrency:
  group: fix-dependabot-ci-${{ github.event.workflow_run.head_branch }}-${{ github.event.workflow_run.conclusion }}

engine:
  id: codex
  # The address GitHub gives github-actions[bot] on the commits it creates, so the
  # sign-off below matches the author however the commits are pushed.
  env:
    GIT_AUTHOR_EMAIL: 41898282+github-actions[bot]@users.noreply.github.com
    GIT_COMMITTER_EMAIL: 41898282+github-actions[bot]@users.noreply.github.com
model: openai/gpt-5

checkout:
  fetch: ["dependabot/uv/*"]
  fetch-depth: 0

network:
  allowed: [defaults, python]

steps:
  - name: Set up the Python versions CI uses
    uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0
    with:
      python-version: |
        3.10
        3.11
        3.12
        3.13
        3.14
  - name: Install uv
    uses: astral-sh/setup-uv@1db35dd8eee11c5894872e0b383ae6c406cf738d # v10.4.0
    with:
      enable-cache: false
  - name: Save the logs of the failed checks
    env:
      GH_TOKEN: ${{ github.token }}
      RUN_ID: ${{ github.event.workflow_run.id }}
    run: gh run view "$RUN_ID" --repo "$GITHUB_REPOSITORY" --log-failed > /tmp/gh-aw/failed-checks.log

tools:
  bash: true

safe-outputs:
  create-pull-request:
    draft: false
    preserve-branch-name: true
    allowed-branches: ["fix/dependabot/uv/**"]
    allowed-files: ["src/**", "pyproject.toml", "uv.lock"]
    protected-files:
      exclude: ["/pyproject.toml", "/uv.lock"]
    fallback-as-issue: false

timeout-minutes: 30
---

# Fix a Dependabot update that fails CI

A check failed on a Dependabot pull request at commit
`${{ github.event.workflow_run.head_sha }}` (run ${{ github.event.workflow_run.html_url }}).
The output of the failed jobs is in `/tmp/gh-aw/failed-checks.log`.

The pull request's commits are authored by `github-actions[bot]` (`GIT_AUTHOR_EMAIL` is
set), and the DCO check wants the author's own sign-off on each of them:

    SIGN_OFF='Signed-off-by: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>'

1. Find Dependabot's branch with
   `git for-each-ref --points-at ${{ github.event.workflow_run.head_sha }} --format='%(refname:lstrip=3)' refs/remotes/origin/dependabot/uv/`.
   If it prints nothing, Dependabot has updated its branch since and a newer run will
   follow. If it prints more than one branch, the commit is not only Dependabot's.
   In both cases stop and call `noop`.
2. Create the branch `fix/<Dependabot's branch>` from the current `main`, and add
   Dependabot's commit with `git cherry-pick ${{ github.event.workflow_run.head_sha }}`.
   If it does not apply cleanly, stop and call `noop` with the reason. Then make
   `github-actions[bot]` its author and add the sign-off above with
   `git commit --amend --no-edit --reset-author --trailer "$SIGN_OFF"`.
3. Install the updated dependencies and reproduce the failure. CI runs these four
   checks on Python 3.10, 3.11, 3.12, 3.13 and 3.14, each with `UV_PYTHON` set to the
   version: `uv run pyright`, `uv run ruff check .`, `uv run ruff format --check .` and
   `uv run pytest`.
4. Find the root cause of every failure and make the smallest correct change to the
   code under `src/` that makes all four checks pass on all five versions. Keep the
   dependency update as Dependabot made it. Do not change anything else.
5. Run the four checks on all five versions again. Continue only when all of them pass.
   Otherwise stop and call `noop` with what still fails.
6. Commit the fix as one commit with `git commit --trailer "$SIGN_OFF"`. The message
   is a Conventional Commit, `fix: <what was wrong>`, with a short body that says why
   the update broke it.
7. Open the pull request with `create_pull_request` from that branch. The title is
   `fix: make CI pass with <dependency> <new version>`. The body is two or three
   sentences on what failed and what the fix changes, then the checks you ran.
