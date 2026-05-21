# Reddit market-review automation — Phase 2 implementation plan

## Objective
Deliver a controlled signal-to-post pipeline with source controls, factor confidence, and explicit operational gates:
1) draft generation,
2) explicit approval,
3) controlled post with throttle.

## Scope delivered in this increment
- Introduced connector/pipeline module for market-review lifecycle in `src/server/core/marketPipeline.ts`.
- Added approved-source filtering for draft confidence computation.
- Added per-factor confidence computation for the 8 market factors.
- Added workflow state machine: `draft -> approved -> posted`.
- Added strict post throttle (minimum 6-hour cool-down between published market-review posts).
- Reworked posting route into gated flow:
  - `POST /internal/menu/post-market-review-draft`
  - `POST /internal/menu/post-market-review-approve`
  - `POST /internal/menu/post-market-review` (publish only if approved + throttle pass)

## Architecture notes
- Redis now stores:
  - latest draft pointer,
  - draft payload/state,
  - last posted timestamp for throttle enforcement.
- Existing market review content generator is preserved and used as markdown source.
- Confidence uses normalized score density against sample count to avoid overfitting to sparse windows.

## Operational flow
1. Run draft action.
2. Inspect draft confidence via toast + stored draft payload.
3. Run approve action.
4. Run publish action.
5. If throttle window is active, publish is denied with retry horizon.

## Next increment (Phase 2b)
- Add external connectors for approved off-Reddit sources (e.g., FRED/event calendar/VIX feed) with adaptor interface.
- Replace lexicon-only confidence with weighted evidence model:
  - source reliability weight,
  - recency decay,
  - engagement quality filtering.
- Add moderation/approval audit trail (approver identity + timestamp).
- Add emergency kill-switch and per-day hard cap.
- Add unit tests for state transitions and throttle edge cases.
