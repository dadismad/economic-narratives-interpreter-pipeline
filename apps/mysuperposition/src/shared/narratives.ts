export type NarrativeSide = 'aligned' | 'contradictory';

export type NarrativeLifecycle = 'emerging' | 'contested' | 'fading';

export type MacroRegime = 'expansionary' | 'neutral' | 'restrictive' | 'tight' | 'loose' | 'sticky' | 'slowing';

export type MacroOverlayItem = {
  key: string;
  label: string;
  regime: MacroRegime;
  delta: string;
  confidence: number; // 0..1
};

export type NarrativeCard = {
  id: string;
  themeId: string;
  title: string;
  summary: string;
  signalStrength: number; // 0..100
  lifecycle: NarrativeLifecycle;
  updatedAt: string; // ISO8601
  sourceCount: number;
};

export type NarrativesOverviewResponse = {
  asOf: string; // ISO8601
  macroOverlay: MacroOverlayItem[];
  aligned: NarrativeCard[];
  contradictory: NarrativeCard[];
};

export type DriverDirection = 'up' | 'down' | 'flat';

export type ThemeDriver = {
  driverId: string;
  label: string;
  direction: DriverDirection;
  confidence: number; // 0..1
};

export type AssetBias = 'bullish' | 'bearish' | 'neutral';

export type ThemeAssetImpact = {
  assetId: string;
  label: string;
  bias: AssetBias;
  confidence: number; // 0..1
};

export type ThemeSummary = {
  themeId: string;
  name: string;
  thesis: string;
  signalStrength: number; // 0..100
  lifecycle: NarrativeLifecycle;
  updatedAt: string; // ISO8601
};

export type ThemeEvidence = {
  id: string;
  source: string;
  snippet: string;
  url?: string;
};

export type ThemeDetailResponse = {
  theme: ThemeSummary;
  drivers: ThemeDriver[];
  assets: ThemeAssetImpact[];
  evidence: ThemeEvidence[];
};

export const LIFECYCLE_COLOR: Record<NarrativeLifecycle, string> = {
  emerging: '#16a34a',
  contested: '#eab308',
  fading: '#dc2626',
};
