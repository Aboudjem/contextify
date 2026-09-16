# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

HazeLab: a bilingual (French default, English) web app to discover, build, and share hookah flavor mixes. Next.js 16 App Router, React 19 with the React Compiler enabled, TypeScript strict, Tailwind CSS v4, shadcn/ui, next-intl, Prisma 7 on Supabase Postgres, Supabase Auth via `@supabase/ssr`. Package manager is pnpm.

## Commands

```bash
pnpm install                 # also runs `prisma generate` (postinstall)
pnpm dev                     # http://localhost:3000 → redirects to /fr
pnpm build                   # prisma generate && next build
pnpm lint                    # eslint (flat config, eslint-config-next)
pnpm tsc --noEmit            # typecheck (no script alias)

# Tests (Vitest 4 + jsdom, no `test` script in package.json)
pnpm vitest run                                          # all tests
pnpm vitest run tests/unit/components/vote-button.test.tsx  # single file
pnpm vitest run -t "renders vote count"                  # single test by name
pnpm vitest                                              # watch mode

# Database
pnpm prisma generate         # regenerate client into src/generated/prisma (gitignored)
pnpm prisma migrate dev      # no migrations/ dir exists yet; first run creates it
pnpm prisma db push          # alternative for quick schema sync
pnpm prisma db seed          # runs tsx prisma/seed.ts (brands, flavors, tags, setups, badges)
pnpm dlx shadcn@latest add <component>   # adds to src/components/ui
```

Env vars come from `.env.local` (copy `.env.local.example`). `prisma.config.ts` loads them via `dotenv`, so Prisma CLI commands work without extra flags. The app degrades without env: middleware skips auth refresh if Supabase vars are missing, and the discover page catches DB errors and renders skeletons. The server Supabase client throws instead.

## Architecture

### Request flow

`src/middleware.ts` runs on every non-API, non-static path. It first calls `updateSession` (`src/lib/supabase/middleware.ts`) to refresh the Supabase auth cookie, then runs the next-intl middleware for locale detection and redirects, and copies the auth cookies onto the intl response. All user-facing routes live under `src/app/[locale]/` (`discover`, `mix`, `prepare`, `community`). `src/app/page.tsx` is the untouched create-next-app placeholder and is never reached because `/` redirects to `/fr`.

Two layouts: `src/app/layout.tsx` (html shell, imports `globals.css`) and `src/app/[locale]/layout.tsx` (validates locale, wraps children in `NextIntlClientProvider`, renders `NavBar` and `LanguageSwitcher`).

### Data access pattern

- **Reads** happen in Server Components using the `prisma` singleton from `src/lib/prisma.ts`. It uses the Prisma 7 driver-adapter setup: a `pg` `Pool` wrapped in `PrismaPg`, and the client is imported from the generated path `@/generated/prisma/client`, not from `@prisma/client`. The seed script builds its own client the same way.
- **Mutations** are Server Actions in `src/actions/` (`"use server"`). Pattern in `vote.ts`: get the Supabase user with `supabase.auth.getUser()`, resolve the app `User` row via `User.supabaseId`, then mutate with Prisma. Return `{ error }` objects rather than throwing.
- **Client interactivity** uses `useOptimistic` + `useTransition` calling the server action directly (see `src/components/community/vote-button.tsx`). Tests mock server actions with `vi.mock("@/actions/...")`.
- Supabase Auth identity and the Prisma `User` table are separate: `User.supabaseId` links them. `Mix.voteCount` is a denormalized counter updated inside the vote action, not computed.
- The OAuth code exchange lives at `src/app/api/auth/callback/route.ts`.

### Domain model (prisma/schema.prisma)

Every `Flavor` carries a 4-axis profile (`sweetness`, `freshness`, `intensity`, `smokiness`, 1–10). A `Mix` is a set of `MixIngredient` rows whose `ratio` values sum to 100; the mix builder (`src/components/mix/mix-builder.tsx`) keeps them balanced client-side and derives a weighted profile for the radar. `SetupType` + ordered `PreparationStep` drive the prepare flow. Structured `Feedback` uses enums (worked/heat/accuracy/duration/wouldSmoke) rather than free-text ratings. All columns are snake_case via `@map`; bilingual content is stored as paired `*En`/`*Fr` columns.

### i18n

Locales `["fr", "en"]`, default `fr`, defined in `src/i18n/routing.ts`. Messages are one file per locale, `messages/fr.json` and `messages/en.json`, keyed by namespace (`nav`, `discover`, `mix`, ...). Both files must stay in sync. Always import `Link`, `useRouter`, `usePathname`, `redirect` from `@/i18n/navigation`, never from `next/link` or `next/navigation`, so locale prefixes are preserved. Server Components use `getTranslations("ns")`; Client Components use `useTranslations("ns")`.

### Styling

Tailwind v4 is CSS-first: all theme tokens are in `src/app/globals.css` under `@theme inline`; there is no `tailwind.config`. Two custom palettes are defined there and used throughout components: `haze-*` (amber accent, e.g. `bg-haze-400`) and `smoke-*` (dark neutrals, e.g. `bg-smoke-700`, `text-smoke-200`), plus the `animate-vote-pop` animation. shadcn semantic tokens (`bg-background`, `text-muted-foreground`) also exist. shadcn components (new-york style, `radix-ui` unified package, lucide icons) live in `src/components/ui`; `cn()` is in `src/lib/utils.ts`. The `glass` and `card-premium` classes referenced in `mix-builder.tsx` are not defined anywhere yet.

## Docs vs. code

`docs/architecture.md`, `docs/plans/2026-02-09-hazelab-mvp.md`, and `docs/research/ux-ui-design-research.md` are the original design references (personas, flows, palette rationale, gotchas). They predate the implementation and differ from the code in several places; trust the code where they conflict:

- Docs say Next.js 15; the project is on Next.js 16 with `reactCompiler: true`.
- Docs show the `prisma-client-js` generator and `@prisma/client` imports; the code uses the `prisma-client` generator with an output dir and the `pg` driver adapter.
- Docs use `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`; the code and `.env.local.example` use `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Docs describe per-namespace message files under `messages/{locale}/`; the code uses a single `messages/{locale}.json`.
- `next-themes`, `zod`, `react-hook-form`, and Playwright are listed in the docs but not installed.

The gotchas section of `docs/architecture.md` (section 9) is still accurate and worth reading before touching auth, Prisma, or next-intl: `await cookies()` and `await params`, use `getUser()` never `getSession()`, keep the Prisma singleton, and Tailwind v4 has no config file.
