export type SignalBucket =
  | 'risk_on'
  | 'risk_off'
  | 'momentum'
  | 'mean_reversion'
  | 'vol_regime'
  | 'liquidity'
  | 'positioning_squeeze'
  | 'event_dislocation';

export type SignalScore = Record<SignalBucket, number>;

export type SignalSample = {
  subreddit: string;
  title: string;
  body?: string;
  score?: number;
  comments?: number;
  createdAt?: Date;
  permalink?: string;
};

const LEXICON: Record<SignalBucket, string[]> = {
  risk_on: ['risk-on', 'risk on', 'growth', 'beta', 'rally', 'bullish', 'melt-up'],
  risk_off: ['risk-off', 'risk off', 'flight to safety', 'defensive', 'drawdown', 'bearish', 'de-risk'],
  momentum: ['breakout', 'trend', 'momentum', 'follow-through', 'relative strength', 'chasing'],
  mean_reversion: ['mean reversion', 'overbought', 'oversold', 'snapback', 'revert', 'pullback'],
  vol_regime: ['volatility', 'vol', 'vix', 'dispersion', 'gamma', 'realized vol', 'implied vol'],
  liquidity: ['liquidity', 'bid-ask', 'depth', 'slippage', 'funding', 'credit spread', 'repo'],
  positioning_squeeze: ['short squeeze', 'gamma squeeze', 'positioning', 'crowded', 'unwind', 'forced covering'],
  event_dislocation: ['cpi', 'fomc', 'nfp', 'earnings', 'guidance', 'downgrade', 'surprise', 'geopolitical'],
};

const emptyScore = (): SignalScore => ({
  risk_on: 0,
  risk_off: 0,
  momentum: 0,
  mean_reversion: 0,
  vol_regime: 0,
  liquidity: 0,
  positioning_squeeze: 0,
  event_dislocation: 0,
});

export function scoreSignals(samples: SignalSample[]): SignalScore {
  const score = emptyScore();

  for (const sample of samples) {
    const text = `${sample.title ?? ''} ${sample.body ?? ''}`.toLowerCase();
    for (const bucket of Object.keys(LEXICON) as SignalBucket[]) {
      for (const term of LEXICON[bucket]) {
        if (text.includes(term)) {
          score[bucket] += 1;
        }
      }
    }
  }

  return score;
}

export function topSignals(score: SignalScore, n = 3): Array<{ bucket: SignalBucket; score: number }> {
  return (Object.entries(score) as Array<[SignalBucket, number]>)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([bucket, v]) => ({ bucket, score: v }));
}
