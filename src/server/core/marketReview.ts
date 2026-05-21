import { reddit } from '@devvit/web/server';
import { scoreSignals, topSignals, type SignalBucket, type SignalSample } from './marketSignals';

const SOURCE_SUBREDDITS = [
  // Economics / macro
  'economics',
  'askeconomics',
  'economy',
  'inflation',
  // Finance / markets
  'finance',
  'investing',
  'stocks',
  'stockmarket',
  'SecurityAnalysis',
  'ValueInvesting',
  'options',
  'quant',
  'algotrading',
  'bonds',
  // Geopolitics / policy risk
  'geopolitics',
  'worldnews',
  'war',
  'ukraine',
  'China',
  'Europe',
  'energy',
  'commodities',
] as const;

const MAX_SUBREDDITS_PER_SWEEP = 18;
const LIMIT_PER_SUBREDDIT = 15;

const getString = (obj: unknown, key: string): string => {
  if (typeof obj !== 'object' || obj === null) {
    return '';
  }
  const value = Reflect.get(obj, key);
  return typeof value === 'string' ? value : '';
};

const getNumber = (obj: unknown, key: string): number => {
  if (typeof obj !== 'object' || obj === null) {
    return 0;
  }
  const value = Reflect.get(obj, key);
  return typeof value === 'number' ? value : 0;
};

type AssetProjection = {
  theme: SignalBucket;
  proxyAssets: string[];
  expectedMovePct: string;
  confidence: number;
  rationale: string;
};

const projectionFromFactor = (factor: SignalBucket, confidence: number): AssetProjection => {
  if (factor === 'risk_on') {
    return {
      theme: factor,
      proxyAssets: ['SPY', 'QQQ', 'HYG'],
      expectedMovePct: confidence >= 0.6 ? '+2% to +5% (1-4w)' : '+0.5% to +2% (1-4w)',
      confidence,
      rationale: 'Breadth and beta-seeking language is elevated.',
    };
  }

  if (factor === 'risk_off') {
    return {
      theme: factor,
      proxyAssets: ['TLT', 'UUP', 'GLD'],
      expectedMovePct: confidence >= 0.6 ? '+1.5% to +4% (1-4w)' : '+0.5% to +1.5% (1-4w)',
      confidence,
      rationale: 'Defensive flow and drawdown framing dominates marginal discourse.',
    };
  }

  if (factor === 'vol_regime') {
    return {
      theme: factor,
      proxyAssets: ['VIX futures', 'tail-risk hedges', 'short-duration cash'],
      expectedMovePct: confidence >= 0.6 ? '+10% to +25% vol products (days-weeks)' : '+3% to +10% vol products (days-weeks)',
      confidence,
      rationale: 'Volatility and gamma-related terms are clustering.',
    };
  }

  if (factor === 'liquidity') {
    return {
      theme: factor,
      proxyAssets: ['IG credit', 'HY credit', 'small caps'],
      expectedMovePct: confidence >= 0.6 ? '+1% to +3% (2-6w)' : '+0% to +1.5% (2-6w)',
      confidence,
      rationale: 'Liquidity and funding language suggests repricing in risk premia.',
    };
  }

  if (factor === 'positioning_squeeze') {
    return {
      theme: factor,
      proxyAssets: ['crowded short baskets', 'high short-interest equities'],
      expectedMovePct: confidence >= 0.6 ? '+5% to +15% (days)' : '+2% to +7% (days)',
      confidence,
      rationale: 'Squeeze/unwind language indicates reflexive positioning risk.',
    };
  }

  if (factor === 'event_dislocation') {
    return {
      theme: factor,
      proxyAssets: ['index futures around macro events', 'rates front-end'],
      expectedMovePct: confidence >= 0.6 ? '±1.5% to ±3% event windows' : '±0.5% to ±1.5% event windows',
      confidence,
      rationale: 'Event-driven catalysts (CPI/FOMC/earnings/geopolitics) are concentrated.',
    };
  }

  if (factor === 'momentum') {
    return {
      theme: factor,
      proxyAssets: ['momentum factor baskets', 'growth beta'],
      expectedMovePct: confidence >= 0.6 ? '+2% to +6% (2-6w)' : '+0.5% to +2.5% (2-6w)',
      confidence,
      rationale: 'Trend-following language dominates over mean-reversion framing.',
    };
  }

  return {
    theme: factor,
    proxyAssets: ['quality factor baskets', 'defensive sectors'],
    expectedMovePct: confidence >= 0.6 ? '+1% to +3% (2-6w)' : '+0% to +1.5% (2-6w)',
    confidence,
    rationale: 'Reversion language is present, suggesting dispersion compression.',
  };
};

export async function collectMarketSamples(limitPerSubreddit = LIMIT_PER_SUBREDDIT): Promise<SignalSample[]> {
  const selectedSubs = SOURCE_SUBREDDITS.slice(0, MAX_SUBREDDITS_PER_SWEEP);

  const batches = await Promise.all(
    selectedSubs.map(async (subreddit) => {
      const posts = await reddit
        .getNewPosts({
          subredditName: subreddit,
          limit: limitPerSubreddit,
          pageSize: Math.min(limitPerSubreddit, 25),
        })
        .all();

      return posts.map((post) => ({
        subreddit,
        title: getString(post, 'title'),
        body: getString(post, 'body'),
        permalink: getString(post, 'permalink'),
        score: getNumber(post, 'score'),
        comments: getNumber(post, 'numComments'),
      }));
    })
  );

  return batches.flat();
}

export async function buildMarketReviewMarkdown(): Promise<string> {
  const samples = await collectMarketSamples();
  const scores = scoreSignals(samples);
  const leaders = topSignals(scores, 4);
  const sampleCount = samples.length;

  const confidence = leaders.map((item) => ({
    factor: item.bucket,
    confidence: sampleCount > 0 ? Math.min(0.95, Math.round((item.score / Math.max(8, sampleCount * 0.18)) * 100) / 100) : 0,
  }));

  const projections = confidence.map((item) => projectionFromFactor(item.factor, item.confidence));

  const factorLine = confidence
    .map((x) => `${x.factor.replace(/_/g, ' ')} (${Math.round(x.confidence * 100)}%)`)
    .join(', ');

  const projectionLines = projections
    .map(
      (x) =>
        `- **${x.theme.replace(/_/g, ' ')}** | proxies: ${x.proxyAssets.join(', ')} | model band: ${x.expectedMovePct} | confidence: ${Math.round(
          x.confidence * 100
        )}%`
    )
    .join('\n');

  const sampleBullets = samples
    .filter((s) => s.title)
    .slice(0, 10)
    .map((s) => `- r/${s.subreddit}: ${s.title}`)
    .join('\n');

  return [
    '## Convergence Market Review (Economics + Finance + Geopolitics)',
    '',
    `Coverage universe: ${sampleCount} recent posts across economics/finance/geopolitics communities.`,
    '',
    `Top converging factors: ${factorLine || 'insufficient signal density'}.`,
    '',
    '### Model-implied potential appreciation / repricing bands',
    projectionLines || '- No robust projections in this sweep.',
    '',
    '### Risk controls (CFA/hedge-fund style framing)',
    '- These are **scenario bands**, not target prices or investment advice.',
    '- Apply position sizing, volatility targeting, and event-risk hedging before execution.',
    '- Confirm with primary data (filings, macro prints, positioning, liquidity) before deployment.',
    '',
    '### Sample narrative flow',
    sampleBullets || '- No eligible posts found in this window.',
  ].join('\n');
}
