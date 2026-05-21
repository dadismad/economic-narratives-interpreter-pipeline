# Repo context consolidation for single-repo agents

This repository now vendors the Devvit app as a Git subtree:

- Path: `apps/mysuperposition`
- Upstream: `https://github.com/dadismad/mysuperposition`

## Why
Some coding agents accept only one repository context. Consolidating related code into a single repo gives the agent full visibility across pipeline + app code.

## Update from upstream
From repo root:

```bash
git fetch mysuperposition main
git subtree pull --prefix=apps/mysuperposition mysuperposition main --squash
```

## Push subtree changes back upstream
If changes are made under `apps/mysuperposition` and should be published to the standalone app repo:

```bash
git subtree push --prefix=apps/mysuperposition mysuperposition main
```

## Notes
- `--squash` keeps host repository history clean.
- Keep cross-repo interfaces documented (data contracts, API payloads) so website agents can operate from one repo context.
