# Economic Narratives Interpreter Pipeline

Pipeline and operations repository for economics/finance/geopolitics narrative intelligence.

## What is in this repository

- `src/` — ingestion, extraction, schemas, storage, CLI orchestration
- `docs/` — source reviews, backlog, runbook notes, convergence outputs
- `tests/` — unit tests for extraction and manifests
- `apps/mysuperposition/` — vendored Devvit app (Git subtree from `dadismad/mysuperposition`)

## Single-repo agent context (important)

If your coding agent can only load one repository, use this repository as the canonical context.
It includes both:

1. **Pipeline code** (ingestion/extraction/manifests)
2. **Devvit app code** under `apps/mysuperposition/`

### Key files for agents

- Pipeline CLI: `src/cli.py`
- Narrative extraction: `src/processing/narrative_extractor.py`
- Storage/manifests: `src/storage/jsonl_store.py`
- Devvit market review logic: `apps/mysuperposition/src/server/core/marketReview.ts`
- Devvit draft/approve/post flow: `apps/mysuperposition/src/server/core/marketPipeline.ts`
- Devvit menu endpoints: `apps/mysuperposition/src/server/routes/menu.ts`

## Subtree sync commands

See `docs/repo_context_and_subtree_sync.md`.

Quick commands:

```bash
# Pull latest from standalone mysuperposition repo into subtree
git fetch mysuperposition main
git subtree pull --prefix=apps/mysuperposition mysuperposition main --squash

# Push subtree changes back to standalone repo
git subtree push --prefix=apps/mysuperposition mysuperposition main
```

## Notes

- Generated runtime data is ignored by git (`data/` in `.gitignore`).
- Keep secrets in `.env`/secret stores; never commit credentials.
