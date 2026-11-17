# Bilance Frontend

React + TypeScript SPA for Bilance, built with Vite.

## Setup

```bash
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:5000` (see
`vite.config.ts`). Point it at a different backend with `VITE_API_URL` in a
local `.env` file.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Typecheck and build for production |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint |

## Project structure

```
src/
├── api/            axios client + per-resource API functions
├── components/
│   ├── layout/     app shell (sidebar, header, notification bell)
│   └── ui/         shared components (Select, DatePicker, Pagination, ...)
├── hooks/          TanStack Query hooks, one section per resource
├── pages/          route-level pages, grouped by feature
├── stores/         Zustand stores (auth, ui)
├── styles/         global SCSS (design tokens, reset)
└── types/          shared TypeScript types mirroring backend schemas
```

State is split deliberately: TanStack Query owns anything that comes from
the API (with query keys mirroring the request params, so different
filter/sort/page combinations cache independently); Zustand only holds
client-only state (auth session, sidebar/theme).

## Deployment

The built app (`dist/`) is static, so it can be hosted anywhere. It is
currently deployed to two places by the CI workflow
([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) on every push to
`main`:

- **Vercel**: job `deploy-frontend`. Deep links work because of the rewrite in
  `vercel.json`.
- **AWS S3 + CloudFront**: job `deploy-frontend-aws`. Deep links work because
  CloudFront maps 403/404 responses to `/index.html`. Details in
  [`../infra/README.md`](../infra/README.md#frontend-hosting-s3--cloudfront).

The API address is baked in at build time through `VITE_API_URL` (the host
URL without `/api`). Every new frontend address must also be added to
`CORS_ORIGINS` on the API (see the backend README).

## Backend

See [`../backend/README.md`](../backend/README.md) for running the API
locally.
