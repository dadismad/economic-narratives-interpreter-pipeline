import { Hono } from 'hono';
import type { UiResponse } from '@devvit/web/shared';
import { context } from '@devvit/web/server';
import { createPost } from '../core/post';
import {
  approveLatestDraft,
  createMarketReviewDraft,
  enforcePostThrottle,
  getLatestDraft,
  markDraftPosted,
} from '../core/marketPipeline';

export const menu = new Hono();

menu.post('/post-create', async (c) => {
  try {
    const post = await createPost();

    return c.json<UiResponse>(
      {
        navigateTo: `https://reddit.com/r/${context.subredditName}/comments/${post.id}`,
      },
      200
    );
  } catch (error) {
    console.error(`Error creating post: ${error}`);
    return c.json<UiResponse>(
      {
        showToast: 'Failed to create post',
      },
      400
    );
  }
});

menu.post('/example-form', async (c) => {
  return c.json<UiResponse>(
    {
      showToast: 'Example form action is wired to /internal/form/example-submit.',
    },
    200
  );
});

menu.post('/post-market-review-draft', async (c) => {
  try {
    const draft = await createMarketReviewDraft();

    const topConfidence = draft.factorConfidence
      .slice(0, 3)
      .map((item) => `${item.factor.replace(/_/g, ' ')} ${Math.round(item.confidence * 100)}%`)
      .join(', ');

    return c.json<UiResponse>(
      {
        showToast: `Draft queued (${draft.sampleCount} samples). Top confidence: ${topConfidence || 'n/a'}`,
      },
      200
    );
  } catch (error) {
    console.error(`Error creating market review draft: ${error}`);
    return c.json<UiResponse>(
      {
        showToast: 'Failed to create market review draft',
      },
      400
    );
  }
});

menu.post('/post-market-review-approve', async (c) => {
  try {
    const approved = await approveLatestDraft();

    if (!approved) {
      return c.json<UiResponse>(
        {
          showToast: 'No draft available to approve',
        },
        400
      );
    }

    return c.json<UiResponse>(
      {
        showToast: `Draft ${approved.id.slice(0, 8)} approved`,
      },
      200
    );
  } catch (error) {
    console.error(`Error approving market review draft: ${error}`);
    return c.json<UiResponse>(
      {
        showToast: 'Failed to approve market review draft',
      },
      400
    );
  }
});

menu.post('/post-market-review', async (c) => {
  try {
    const draft = await getLatestDraft();
    if (!draft) {
      return c.json<UiResponse>({ showToast: 'No draft found. Run draft step first.' }, 400);
    }

    if (draft.stage !== 'approved') {
      return c.json<UiResponse>({ showToast: 'Draft not approved. Approve before posting.' }, 400);
    }

    const throttle = await enforcePostThrottle();
    if (throttle.ok === false) {
      const hours = Math.ceil(throttle.retryAfterMs / (60 * 60 * 1000));
      return c.json<UiResponse>({ showToast: `Posting throttle active. Retry in ~${hours}h.` }, 429);
    }

    const post = await createPost({
      title: `Convergence Review (Econ/Finance/Geopolitics): ${new Date().toISOString().slice(0, 10)}`,
      textFallback: draft.markdown,
    });

    await markDraftPosted(draft.id);

    return c.json<UiResponse>(
      {
        navigateTo: `https://reddit.com/r/${context.subredditName}/comments/${post.id}`,
      },
      200
    );
  } catch (error) {
    console.error(`Error creating market review post: ${error}`);
    return c.json<UiResponse>(
      {
        showToast: 'Failed to create market review post',
      },
      400
    );
  }
});
