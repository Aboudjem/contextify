# Detection signals

Purpose: the file-to-fact-to-section map that turns a repo scan into evidenced AGENTS.md lines, plus what each signal must never be stretched to imply.

Presence of a path is a candidate, not proof: read the file before writing a line from it. (Source: DECISIONS.md D3, the evidence rule.)

## Signal map

| Signal file(s) | Fact it yields | Feeds section | Must NOT be used to infer |
|---|---|---|---|
| `package.json#scripts` | exact build/test/lint/dev command names | Commands | that an unlisted script exists; an npm script name is not a Make target |
| `package.json#packageManager` | which manager governs install and script invocation | Commands | the manager from a lockfile alone when `packageManager` disagrees; `packageManager` wins |
| `package.json#engines` | a pinned runtime version | Commands | a version range as a single exact version; quote the range as written |
| `package.json#workspaces`, `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json` | monorepo membership, which dirs are build units | Architecture, size class | that every listed package is independently deployed; check for its own manifest and CI job |
| Lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`/`bun.lock`) | which package manager last ran, presence only | Commands | dependency versions as claims; only presence is hashed |
| `Makefile`/`justfile`/`GNUmakefile`/`Justfile` | literal build/test/run targets and their recipes | Commands | that a target name implies a language; read the recipe body |
| `pyproject.toml` `[project.scripts]`/`[project.gui-scripts]`, Poetry script mappings | named entry-point commands | Commands | a dependency name as a runnable command; only a declared script target resolves |
| `Cargo.toml` bins, `autobins`, `Cargo.lock` workspace members | buildable binary names, workspace membership | Commands, Architecture | crate version as a verified claim; dependency versions are excluded |
| `go.mod` module path and `go` directive | module path, minimum Go version | Commands, Conventions | `require` entries as verified dependency facts |
| `Gemfile`, `pom.xml`, `build.gradle[.kts]`, `settings.gradle[.kts]` | presence of a Ruby or JVM build, by filename only | Commands | contents or dependency versions; only presence is hashed |
| `tsconfig.json`, `tsconfig.*.json` (`paths`/`strict`/`target`/`module`) | import alias map, strictness, target, module system | Conventions | every other compiler option; only these four fields are hashed |
| `.github/workflows/*.yml`, `.gitlab-ci.yml` (jobs, `run:` lines) | the commands CI actually runs, working directories, which job gates a PR | Commands, Boundaries (Always) | a workflow's filename as its trigger; read the `on:` block |
| `Dockerfile`, `*/Dockerfile` (`FROM`/`EXPOSE`) | base image identity, exposed ports | Architecture | that an exposed port is the port the app is reachable on in production; check the deploy config too |
| `docker-compose.yml`/`compose.yml`/`compose.yaml` service names | local service topology | Architecture | that compose service names match production infrastructure names |
| `.env.example`/`.env.sample`/`.env.template` variable names | required configuration surface, names only | Conventions, Testing | values; never read past `=` |
| `vercel.json`/`netlify.toml`/`fly.toml`/`render.yaml`/`Procfile`/`serverless.yml`/`amplify.yml`/`apprunner.yaml`/`cdk.json`, Terraform files, k8s manifests | which platform hosts the app, that a deploy config exists | Repository workflow, Boundaries (Ask first) | that the config alone proves auto-deploy on push; confirm the trigger in CI or the platform's own settings |
| `prisma/schema.prisma` | an ORM-managed schema exists, migration tooling is Prisma | Architecture, Boundaries | the database engine from the ORM name alone; read the `datasource` block |
| `supabase/` directory | Supabase is used for local dev, likely for the backend | Architecture | that Supabase is the production database without a matching env var or IaC reference |
| Test configs (`vitest.config.*`, `jest.config.*`, `pytest.ini`/`pyproject.toml [tool.pytest]`, `playwright.config.*`) | which runner owns which test tier, fixture setup | Testing | that a config file's presence means tests currently pass; only that a runner is wired |
| `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` | contribution rules and review expectations already stated by the repo | Repository workflow | a convention as enforced just because it is written; check whether CI or branch protection also enforces it |
| Release workflows (`.github/workflows/release*.yml`, tag-triggered jobs) | how a release is cut, whether it is automated | Repository workflow | that a manual release script implies automatic deploy; these are separate facts |
| `@generated`, `DO NOT EDIT`, `linguist-generated` markers | generated code that must not be hand-edited | Boundaries (Never) | that every file in the same directory is also generated; the marker must be on the specific file |
| Tracked migrations directories (`prisma/migrations/`, `migrations/`, `db/migrate/`) | schema changes are tracked and reviewable | Boundaries (Ask first) | that migrations always need approval; only when the migration also runs against a shared environment on merge |

Two general cautions that apply across every row: a branch named `prod` is not proof it deploys anywhere, and a branch named `main` is not proof it is the default; confirm from CI or IaC, never from the name. Likewise a `src/` directory is not proof of any particular framework; the manifest and lockfile are the primary source, not the folder layout.

## Boundaries detectors (D4)

| Detector | Evidence | Label | Example line |
|---|---|---|---|
| Gating CI command | a workflow on `pull_request` whose `run:` line matches a Commands entry | Always | `Always: run \`pnpm run typecheck\` before opening a PR, it is the \`pull_request\` gate in CI` |
| Deploy on push to the default branch | CI or platform config triggers deploy on push to the branch that is actually the default | Ask first | `Ask first: pushing to \`main\`, it auto-deploys on merge` |
| Tracked migrations directory | a framework-recognized migrations dir exists and is tracked | Ask first | `Ask first: touching \`prisma/migrations/\`, it runs against shared staging on merge` |
| Generated code markers | `@generated`, `DO NOT EDIT`, or `linguist-generated` found in a tracked file | Never | `Never: hand-edit \`src/generated/api.ts\`, regenerate it instead` |
| Tracked `.env.example` with `.env` ignored | `.env.example` tracked, `.env` listed in `.gitignore` | Never | `Never: commit a real value into \`.env\`, \`.env.example\` is the template` |

A deploy script proves deployment exists, not that it needs approval; that permission comes from an existing policy or a recorded human decision, not from the presence of the script alone. (Source: DECISIONS.md D4.)

## Hazard patterns that justify a Never line

- A tracked `.env` carrying real-looking values, not just `.env.example`: the clearest Never, evidenced directly.
- Generated code markers (`@generated`, `DO NOT EDIT`, `linguist-generated`): never hand-edit the marked file, name the regeneration command instead.
- A force-push or history-rewrite rule already stated in `CONTRIBUTING.md`: surface the repo's own stated rule as a Never line, sourced to the file, never invented.
- A shared production resource named in IaC (a Terraform resource or k8s manifest whose name states it is prod, or that more than one service references): never touch it without coordinating across consumers, only when the IaC itself names it shared.

Two of the five items commonly assumed to be Never are actually Ask first per the D4 detector table above: a tracked migrations directory, and a deploy trigger on push to the default branch. Neither blocks the action outright; both require a human in the loop before proceeding.
