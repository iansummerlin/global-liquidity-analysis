---
description: Commit with conventional commit message and push. Optionally run tests first.
---

First, look at the staged/unstaged changes to judge whether tests are needed:
- Run `git diff --stat HEAD` to see what files changed

If the changes touch any Python logic files (data/, features/, evaluation/, signals/, scripts/, config.py, main.py, etc.), check whether tests have recently passed before deciding to run them:

```bash
STAMP=/tmp/gla_last_test_run
if [ -f "$STAMP" ]; then
  LAST=$(cat "$STAMP")
  NOW=$(date +%s)
  AGE=$((NOW - LAST))
  if [ $AGE -lt 300 ]; then
    echo "Tests passed ${AGE}s ago — skipping re-run"
    SKIP_TESTS=1
  fi
fi
```

If `SKIP_TESTS` is not set, run tests:
1. Run `cd /home/ixn/Documents/code/crypto/global-liquidity-analysis && .venv/bin/python -m pytest tests/ -v`
   - If tests fail: show a summary of failures, STOP — do NOT commit or push, do NOT attempt to fix errors automatically
   - If tests pass: record the timestamp and continue:
     ```bash
     date +%s > /tmp/gla_last_test_run
     ```

If the changes are trivial (docs, comments, config templates, markdown, command files, .gitignore, etc.), skip tests and continue directly.

Then:
2. Run `git add .` to stage all changes
3. Run `git status` and `git diff --staged` to review what will be committed
4. Commit with a conventional commit message (feat:, fix:, refactor:, chore:, docs:, test:, etc.)
5. Push to the remote branch
