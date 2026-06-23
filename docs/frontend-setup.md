# Frontend setup

This project uses a Vite + React SPA because the frontend is an internal tool that mainly needs fast iteration, authenticated app flows, and a clean connection to the FastAPI backend. We do not need the extra server-rendering, SEO, or full-stack routing features that Next.js is optimized for.

## Init (from empty `frontend/`)

```bash
cd frontend
pnpm create vite . --template react-ts
pnpm install
pnpm add -D tailwindcss @tailwindcss/vite
```

Wire up Tailwind and the `@/*` import alias before running shadcn:

1. Add `@import "tailwindcss";` to the top of `src/index.css`.
2. Add the `@tailwindcss/vite` plugin and `@` alias to `vite.config.ts`.
3. Add `baseUrl` + `paths` for `@/*` to `tsconfig.json` and `tsconfig.app.json`.

See [shadcn Vite install](https://ui.shadcn.com/docs/installation/vite#existing-project) for the exact snippets.

Then:

```bash
pnpm dlx shadcn@latest init
```

## Run

```bash
cd frontend
pnpm install
pnpm dev
```

## Check

```bash
pnpm tsc --noEmit
pnpm lint
```

