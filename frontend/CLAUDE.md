# Frontend — Next.js (App Router)

This is the Vercel-hosted Next.js app. It talks to the Python backend **only over HTTP**, never by import.

## Rules

- **No imports from `backend/`.** The two trees are deployed and run separately. Cross only via HTTP.
- All backend calls go through `lib/api/` (one place — easy to swap base URL, add auth, etc.).
- Base URL comes from `process.env.NEXT_PUBLIC_API_BASE_URL` (defaults to `/api`, which Vercel routes to the Python function).
- Prefer **Server Components** for data fetching; reach for `"use client"` only when you need interactivity (state, effects, event handlers).
- Tailwind for styling. Keep design tokens in `tailwind.config.ts`, not scattered in components.

## Structure

| Path | Purpose |
|---|---|
| `app/` | Routes (App Router). `layout.tsx` is the root shell, `page.tsx` is `/`. |
| `components/` | Reusable React components. |
| `lib/` | Non-component code: API client, hooks, utilities. |
| `public/` | Static assets served at `/`. |

## Run

```bash
npm install
npm run dev          # http://localhost:3000
npm run build
npm run typecheck
```
