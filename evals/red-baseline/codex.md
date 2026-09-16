# Repository Guidelines

HazeLab is a bilingual hookah flavor and mix application. The current stack is Next.js 16.1.6 (App Router), React 19.2.3, strict TypeScript, Tailwind CSS 4, Prisma 7, and Supabase authentication. Treat `package.json` and executable configuration as authoritative: `docs/architecture.md` contains older Next.js 15 guidance and planned dependencies that are not installed.

## Project Structure

- `src/app/`: layouts, global styles, localized pages, and the authentication callback. Feature pages live under `src/app/[locale]/`.
- `src/components/`: feature components grouped by domain; shared UI primitives are in `src/components/ui/`.
- `src/actions/`: server actions, including authenticated voting.
- `src/lib/`: shared utilities, Prisma singleton, and separate Supabase browser/server/middleware clients.
- `src/i18n/` and `messages/`: locale routing and French/English translations. French is the default locale.
- `prisma/`: database schema and seed data. `tests/unit/` contains Vitest tests.
- `docs/`: architectural background, design research, and implementation plans; check proposals against current code.

## Setup and Commands

Use pnpm, consistent with `pnpm-lock.yaml`. Populate a local environment file from `.env.local.example`, including the Supabase URL, anonymous key, and `DATABASE_URL`. Keep credentials out of version control.

| Command | Purpose |
| --- | --- |
| `pnpm install` | Install dependencies; postinstall generates the Prisma client. |
| `pnpm dev` | Start the development server at localhost:3000. |
| `pnpm build` | Generate the Prisma client, then build Next.js. |
| `pnpm start` | Serve a completed production build. |
| `pnpm lint` | Run ESLint with Next.js and TypeScript rules. |
| `pnpm exec vitest run` | Run the configured unit/component tests once. |

There is no package test script; Vitest is configured in `vitest.config.ts`. Prisma configuration and the seed import `dotenv/config`: ensure `DATABASE_URL` is available to those processes; do not assume they load Next.js's local environment file automatically.

## Coding Conventions

Follow surrounding TypeScript/TSX style: two-space indentation, double quotes, semicolons, PascalCase component exports, and kebab-case component filenames. Use the `@/*` alias for imports from `src/`.

Keep interactive components behind an explicit client boundary and database access in server code. Reuse `src/lib/prisma.ts` and the appropriate Supabase helper. Follow the authentication checks in `src/actions/vote.ts` for protected mutations.

Reuse UI primitives and the tokens in `src/app/globals.css`. Use locale-aware navigation from `src/i18n/navigation.ts`; update both `messages/fr.json` and `messages/en.json` when adding translated copy.

## Testing and Review

Place tests under `tests/` using `*.test.ts` or `*.test.tsx` filenames. Vitest uses jsdom and React Testing Library; existing component tests demonstrate mocking server actions. Cover changed behavior and failure cases.

For application changes, run lint, relevant tests, and the build; report any environment blockers explicitly. Check affected UI in both locales. PRs should explain the behavior change, validation performed, and include screenshots for visual changes. Use concise, imperative commit subjects; the available history does not establish a commit-prefix convention. Commit using the user's configured Git identity without per-command overrides.

## Database and Generated Files

Do not hand-edit or commit the generated Prisma client; its output is ignored by Git. Change `prisma/schema.prisma` and regenerate through the build instead. The seed writes to the database selected by `DATABASE_URL`; verify the target before running it or schema-changing operations. No migration history or deployment workflow is checked in, so confirm the intended database/release procedure before introducing one.
