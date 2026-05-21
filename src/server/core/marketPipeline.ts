import { redis, context } from '@devvit/web/server';
import { buildMarketReviewMarkdown, collectMarketSamples } from './marketReview';
import { scoreSignals, type SignalBucket, type SignalSample, type SignalScore } from './marketSignals';

const APPROVED_SOURCES = [
  'economics',
  'askeconomics',
  'economy',
  'inflation',
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
  'geopolitics',
  'worldnews',
  'war',
  'ukraine',
  'China',
  'Europe',
  'energy',
  'commodities',
] as const;
const DRAFT_POINTER_KEY = 'market_review:latest_draft_id';
const DRAFT_KEY_PREFIX = 'market_review:draft:';
const LAST_POSTED_AT_KEY = 'market_review:last_posted_at';
const MIN_POST_INTERVAL_MS = 24 * 60 * 60 * 1000;

type ReviewStage = 'draft' | 'approved' | 'posted';

export type FactorConfidence = {
  factor: SignalBucket;
  score: number;
  confidence: number;
};

export type ReviewDraft = {
  id: string;
  generatedAt: string;
  generatedBySubreddit: string;
  stage: ReviewStage;
  markdown: string;
  sampleCount: number;
  factorConfidence: FactorConfidence[];
};

const confidenceFromScore = (score: number, sampleCount: number): number => {
  if (sampleCount <= 0 || score <= 0) {
    return 0;
  }

  const normalized = Math.min(1, score / Math.max(6, sampleCount * 0.2));
  return Math.round(normalized * 100) / 100;
};

const factorConfidence = (scores: SignalScore, sampleCount: number): FactorConfidence[] => {
  const entries = Object.entries(scores) as Array<[SignalBucket, number]>;

  return entries
    .map(([factor, score]) => ({
      factor,
      score,
      confidence: confidenceFromScore(score, sampleCount),
    }))
    .sort((a, b) => b.confidence - a.confidence || b.score - a.score);
};

const draftKey = (id: string): string => `${DRAFT_KEY_PREFIX}${id}`;

const parseDraft = (raw: string | null | undefined): ReviewDraft | null => {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }

    const maybeId = 'id' in parsed ? parsed.id : null;
    const maybeStage = 'stage' in parsed ? parsed.stage : null;
    const maybeMarkdown = 'markdown' in parsed ? parsed.markdown : null;
    const maybeGeneratedAt = 'generatedAt' in parsed ? parsed.generatedAt : null;
    const maybeGeneratedBySubreddit = 'generatedBySubreddit' in parsed ? parsed.generatedBySubreddit : null;
    const maybeSampleCount = 'sampleCount' in parsed ? parsed.sampleCount : null;
    const maybeFactorConfidence = 'factorConfidence' in parsed ? parsed.factorConfidence : null;

    if (
      typeof maybeId !== 'string' ||
      typeof maybeStage !== 'string' ||
      typeof maybeMarkdown !== 'string' ||
      typeof maybeGeneratedAt !== 'string' ||
      typeof maybeGeneratedBySubreddit !== 'string' ||
      typeof maybeSampleCount !== 'number' ||
      !Array.isArray(maybeFactorConfidence)
    ) {
      return null;
    }

    return {
      id: maybeId,
      stage: maybeStage === 'approved' || maybeStage === 'posted' ? maybeStage : 'draft',
      markdown: maybeMarkdown,
      generatedAt: maybeGeneratedAt,
      generatedBySubreddit: maybeGeneratedBySubreddit,
      sampleCount: maybeSampleCount,
      factorConfidence: maybeFactorConfidence
        .filter((item) => item && typeof item === 'object')
        .map((item) => {
          const factor = 'factor' in item && typeof item.factor === 'string' ? item.factor : 'risk_on';
          const score = 'score' in item && typeof item.score === 'number' ? item.score : 0;
          const confidence = 'confidence' in item && typeof item.confidence === 'number' ? item.confidence : 0;

          return {
            factor: factor as SignalBucket,
            score,
            confidence,
          };
        }),
    };
  } catch {
    return null;
  }
};

export async function createMarketReviewDraft(): Promise<ReviewDraft> {
  const samples = await collectMarketSamples();
  const approvedSamples = samples.filter((sample) => APPROVED_SOURCES.includes(sample.subreddit as (typeof APPROVED_SOURCES)[number]));
  const sampleUniverse: SignalSample[] = approvedSamples.length > 0 ? approvedSamples : samples;
  const scores = scoreSignals(sampleUniverse);
  const markdown = await buildMarketReviewMarkdown();

  const draft: ReviewDraft = {
    id: crypto.randomUUID(),
    generatedAt: new Date().toISOString(),
    generatedBySubreddit: context.subredditName,
    stage: 'draft',
    markdown,
    sampleCount: sampleUniverse.length,
    factorConfidence: factorConfidence(scores, sampleUniverse.length),
  };

  await Promise.all([
    redis.set(draftKey(draft.id), JSON.stringify(draft)),
    redis.set(DRAFT_POINTER_KEY, draft.id),
  ]);

  return draft;
}

export async function getLatestDraft(): Promise<ReviewDraft | null> {
  const id = await redis.get(DRAFT_POINTER_KEY);
  if (!id) {
    return null;
  }

  const raw = await redis.get(draftKey(id));
  return parseDraft(raw);
}

export async function approveLatestDraft(): Promise<ReviewDraft | null> {
  const draft = await getLatestDraft();
  if (!draft) {
    return null;
  }

  const approved: ReviewDraft = {
    ...draft,
    stage: 'approved',
  };

  await redis.set(draftKey(approved.id), JSON.stringify(approved));
  return approved;
}

export async function enforcePostThrottle(now = Date.now()): Promise<{ ok: true } | { ok: false; retryAfterMs: number }> {
  const lastPostedAtRaw = await redis.get(LAST_POSTED_AT_KEY);
  if (!lastPostedAtRaw) {
    return { ok: true };
  }

  const lastPostedAt = Number(lastPostedAtRaw);
  if (Number.isNaN(lastPostedAt)) {
    return { ok: true };
  }

  const nextWindow = lastPostedAt + MIN_POST_INTERVAL_MS;
  if (now < nextWindow) {
    return { ok: false, retryAfterMs: nextWindow - now };
  }

  return { ok: true };
}

export async function markDraftPosted(id: string): Promise<void> {
  const raw = await redis.get(draftKey(id));
  const draft = parseDraft(raw);
  if (!draft) {
    return;
  }

  const posted: ReviewDraft = {
    ...draft,
    stage: 'posted',
  };

  await Promise.all([
    redis.set(draftKey(id), JSON.stringify(posted)),
    redis.set(LAST_POSTED_AT_KEY, Date.now().toString()),
  ]);
}
