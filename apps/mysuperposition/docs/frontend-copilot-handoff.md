# Front-Page Implementation Spec (Copilot-Ready)

## 1) Objective
Build the front page for the Economic Narratives Interpreter with:
- Dual narrative columns: `Aligned` vs `Contradictory`
- Signal-strength ranking (strongest narratives first)
- Lifecycle status colors: `green/yellow/red`
- Macro overlay strip (rates/inflation/growth/liquidity regime)
- Drill-down path: `Theme -> Drivers -> Assets`

This package is designed for direct execution by Copilot/Coding Agent with minimal ambiguity.

## 2) Delivery scope (frontend-first)
- Replace placeholder `src/client/game.tsx` UI with a dashboard shell and typed data binding.
- Introduce shared frontend contract types in `src/shared/narratives.ts`.
- Consume backend endpoint payloads (contract below); if endpoint is missing, render with local mock payload behind a feature flag.
- Preserve existing Devvit constraints (`navigateTo`, no window.alert, fast splash).

## 3) Information architecture

### Main layout
- Header: product title, as-of timestamp, last update source, refresh action
- Macro overlay row: 4-6 macro chips (regime + deltas)
- Body split (2 columns):
  - Left: Aligned narratives (supporting dominant macro regime)
  - Right: Contradictory narratives (counter-regime / divergence)
- Sidebar/footer panel: selected theme drill-down (`Drivers`, `Assets`, evidence links)

### User interaction model
1. User opens page -> load overview payload
2. Narratives are sorted by `signalStrength` desc
3. Click a narrative card -> fetch/resolve detail payload
4. Drill-down displays:
   - Theme summary
   - Ranked drivers with confidence
   - Impacted assets with directional bias and confidence

## 4) Component tree (React)

```text
App
├─ PageShell
│  ├─ TopBar
│  │  ├─ TitleBlock
│  │  ├─ AsOfStamp
│  │  └─ RefreshButton
│  ├─ MacroOverlayStrip
│  │  └─ MacroChip[]
│  ├─ NarrativeColumns
│  │  ├─ NarrativeColumn(type='aligned')
│  │  │  └─ NarrativeCard[]
│  │  └─ NarrativeColumn(type='contradictory')
│  │     └─ NarrativeCard[]
│  └─ DrilldownPanel
│     ├─ ThemeSummary
│     ├─ DriversTable
│     └─ AssetsTable
└─ StatusBoundary
   ├─ LoadingState
   ├─ EmptyState
   └─ ErrorState
```

## 5) Data contracts
Source of truth type definitions are in `src/shared/narratives.ts`.

### 5.1 Overview endpoint
`GET /api/narratives/overview`

Response:
- `asOf`: ISO timestamp
- `macroOverlay`: current macro descriptors
- `aligned`: ranked narrative cards
- `contradictory`: ranked narrative cards

### 5.2 Drill-down endpoint
`GET /api/narratives/theme/:themeId`

Response:
- `theme`: selected theme metadata + lifecycle + score
- `drivers`: ranked causal drivers
- `assets`: ranked impacted assets
- `evidence`: optional source links/snippets

### 5.3 Ranking + lifecycle rules
- `signalStrength`: normalize to 0-100 for display bars
- Ranking order: `signalStrength desc`, tie-breaker `updatedAt desc`
- Lifecycle mapping:
  - `emerging` -> green (`#16a34a`)
  - `contested` -> yellow (`#eab308`)
  - `fading` -> red (`#dc2626`)

## 6) API payload examples

### 6.1 Overview sample
```json
{
  "asOf": "2026-05-21T16:20:00Z",
  "macroOverlay": [
    { "key": "rates", "label": "Policy Rates", "regime": "restrictive", "delta": "+25bps", "confidence": 0.82 },
    { "key": "inflation", "label": "Inflation Pulse", "regime": "sticky", "delta": "-0.2pp", "confidence": 0.73 },
    { "key": "growth", "label": "Growth Momentum", "regime": "slowing", "delta": "-0.3pp", "confidence": 0.68 },
    { "key": "liquidity", "label": "Liquidity", "regime": "tight", "delta": "flat", "confidence": 0.66 }
  ],
  "aligned": [
    {
      "id": "nar_001",
      "themeId": "th_rates_higher_longer",
      "title": "Higher-for-longer rates pressure long-duration multiples",
      "summary": "Forum flow points to repricing in speculative growth sleeves.",
      "signalStrength": 89,
      "lifecycle": "emerging",
      "updatedAt": "2026-05-21T16:10:00Z",
      "sourceCount": 42
    }
  ],
  "contradictory": [
    {
      "id": "nar_101",
      "themeId": "th_soft_landing_risk_on",
      "title": "Soft-landing consensus supports cyclical beta",
      "summary": "Contradicts tightening narrative via improving earnings breadth.",
      "signalStrength": 74,
      "lifecycle": "contested",
      "updatedAt": "2026-05-21T16:12:00Z",
      "sourceCount": 31
    }
  ]
}
```

### 6.2 Theme drill-down sample
```json
{
  "theme": {
    "themeId": "th_rates_higher_longer",
    "name": "Higher-for-longer rates",
    "thesis": "Policy path remains restrictive for longer than equity-implied expectations.",
    "signalStrength": 89,
    "lifecycle": "emerging",
    "updatedAt": "2026-05-21T16:10:00Z"
  },
  "drivers": [
    { "driverId": "drv_cpi_sticky", "label": "Sticky core inflation prints", "direction": "up", "confidence": 0.84 },
    { "driverId": "drv_labor_tight", "label": "Tight labor market", "direction": "up", "confidence": 0.78 },
    { "driverId": "drv_term_premium", "label": "Rising term premium", "direction": "up", "confidence": 0.71 }
  ],
  "assets": [
    { "assetId": "NDX", "label": "Nasdaq 100", "bias": "bearish", "confidence": 0.76 },
    { "assetId": "UST10Y", "label": "US 10Y Yield", "bias": "bullish", "confidence": 0.81 },
    { "assetId": "XLF", "label": "US Financials", "bias": "bullish", "confidence": 0.62 }
  ],
  "evidence": [
    {
      "id": "ev_9001",
      "source": "reddit:r/economics",
      "snippet": "...market repricing toward prolonged restrictive stance...",
      "url": "https://reddit.com/..."
    }
  ]
}
```

## 7) Frontend implementation notes for Copilot

1. Create `src/client/components/narratives/*` with the tree in section 4.
2. Add typed client fetchers (`getOverview`, `getThemeDetail`) with runtime guards.
3. Keep central page state:
   - `overview: NarrativesOverviewResponse | null`
   - `selectedThemeId: string | null`
   - `themeDetailById: Record<string, ThemeDetailResponse>`
4. Use skeletons for first paint and optimistic panel loading when selecting cards.
5. Render lifecycle with explicit token mapping (no implicit color logic).
6. Accessibility:
   - Cards keyboard-focusable
   - Color + text labels for lifecycle (no color-only signal)

## 8) Acceptance criteria

### Functional
- [ ] Two visible columns labeled `Aligned` and `Contradictory`.
- [ ] Cards in each column ranked by descending signal strength.
- [ ] Lifecycle badge appears on every card using green/yellow/red mapping.
- [ ] Macro overlay row renders at top with at least 4 chips from payload.
- [ ] Clicking a card opens drill-down showing `Theme`, `Drivers`, `Assets`.
- [ ] Drill-down supports empty evidence gracefully.

### Data/contract
- [ ] Frontend compiles against `src/shared/narratives.ts` with no `any` casts.
- [ ] Unknown enum values degrade safely to `unknown` chip/badge style.
- [ ] Timestamp parsing uses ISO strings and displays deterministic UTC format.

### UX/performance
- [ ] First meaningful paint under 1s for cached payload path.
- [ ] Loading, empty, and error states are explicitly rendered.
- [ ] Keyboard-only navigation covers card selection and panel traversal.

### QA checklist
- [ ] Snapshot test for both columns with mixed lifecycle statuses.
- [ ] Unit test for ranking order + tie-breaker behavior.
- [ ] Unit test for lifecycle color token mapping.
- [ ] Integration test: click card -> drill-down request -> panel render.

## 9) Suggested execution order
1. Contract types + mock fixtures
2. Page shell + macro overlay
3. Dual-column card rendering + ranking
4. Drill-down panel wiring
5. States (loading/error/empty)
6. Tests + polish
