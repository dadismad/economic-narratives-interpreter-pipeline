import { reddit } from '@devvit/web/server';

type CreatePostOptions = {
  title?: string;
  textFallback?: string;
};

type CustomPostPayload = {
  title: string;
  textFallback?: { text: string };
};

export const createPost = async (opts: CreatePostOptions = {}) => {
  const payload: CustomPostPayload = {
    title: opts.title ?? 'mysuperposition',
  };

  if (opts.textFallback) {
    payload.textFallback = { text: opts.textFallback };
  }

  return await reddit.submitCustomPost(payload);
};
