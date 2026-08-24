import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    draft: z.boolean().default(false),
    categories: z.array(z.string()).default([]),
    // 原始 WordPress 信息（便于追溯）
    coverImage: z.string().optional(),
    originalSlug: z.string().optional(),
    originalUrl: z.string().optional(),
  }),
});

export const collections = { blog };
