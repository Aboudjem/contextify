<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/hero-light.svg">
  <img alt="contextify: an AGENTS.md card with line 6 marked stale, linked to a Makefile card where the test-health target is crossed out, a 0 tokens counter, and the install command" src="../assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](../LICENSE)

[English](../README.md) | Français | [Español](es.md) | [日本語](ja.md) | [简体中文](zh-CN.md)

<!-- may-lag -->

**Un seul AGENTS.md pour vos agents, vérifié sans aucun token.**

contextify écrit un fichier d'instructions court et vous avertit quand une ligne n'est plus à jour.

| Temps gagné | Contexte préservé | Tokens économisés |
|:--|:--|:--|
| L'avertissement donne le fichier, la ligne et la commande disparue. Voir l'exemple plus bas. | Un fichier de 20, 40 ou 60 lignes, selon la taille du dépôt. Le renvoi `CLAUDE.md` fait 4 lignes. | La vérification des lignes périmées est un script local. Elle n'appelle aucun modèle, donc elle coûte zéro token. |

**Fonctionne avec :** tout agent qui lit les skills. Testé : Claude Code, Codex.

Lié à aucun modèle : la vérification est en Bash et Python simples.

`AGENTS.md` est le fichier d'instructions que lisent les agents de code. Utilisez contextify si votre dépôt n'en a pas, ou s'il cite d'anciennes commandes.

Vous obtenez un fichier court et un avertissement quand une ligne devient périmée.

```bash
npx skills add Aboudjem/contextify -g
# then, in your agent: contextify init
```

Cette commande l'installe pour tous vos projets. La commande de chaque agent est dans [Installation](#installation).

### Exemple de rapport

Une vraie exécution du 2026-11-17. contextify 0.3.0 a écrit `AGENTS.md` pour un petit service Python.

Puis la cible `test-health` a été supprimée de son `Makefile`. La version 0.3.3 affiche ceci :

```text
contextify: drift
1. Run /contextify:contextify update to fix AGENTS.md:6 (make test-health)
2. Review the diff it shows before it writes
3. Commit the context files with .contextify/
Agents     outside Claude Code, ask for "contextify update"
Scope      .
Stale      AGENTS.md:6 references make test-health
Unverified AGENTS.md:6 python3 -m unittest tests.test_health
Changed    makefile#targets
More       +3 findings
Files      0 written
Accept     unavailable until the stale command is corrected
```

Un dépôt à jour n'affiche rien. Les fichiers et le tampon de cette exécution sont livrés avec l'exemple, vous pouvez donc la rejouer :

```bash
sh examples/python-service-0.3.0/replay.sh
```

[Exécution complète, fichiers et modification qui l'a déclenchée](../examples/python-service-0.3.0/README.md).

**Limite :** il vérifie les commandes, les cibles et les fichiers, pas la prose, et ne les lance jamais.

## Installation

**Choisissez votre agent.** Chaque commande installe contextify pour tous vos projets.

<p align="center">
  <a href="#install-claude-code"><img src="https://img.shields.io/badge/Claude_Code-D97757?style=for-the-badge&logo=claude&logoColor=white" alt="Claude Code"></a>
  <a href="#install-codex"><img src="https://img.shields.io/badge/Codex-000000?style=for-the-badge&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyBmaWxsPSJ3aGl0ZSIgcm9sZT0iaW1nIiB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI%2BPHRpdGxlPk9wZW5BSTwvdGl0bGU%2BPHBhdGggZD0iTTIyLjI4MTkgOS44MjExYTUuOTg0NyA1Ljk4NDcgMCAwIDAtLjUxNTctNC45MTA4IDYuMDQ2MiA2LjA0NjIgMCAwIDAtNi41MDk4LTIuOUE2LjA2NTEgNi4wNjUxIDAgMCAwIDQuOTgwNyA0LjE4MThhNS45ODQ3IDUuOTg0NyAwIDAgMC0zLjk5NzcgMi45IDYuMDQ2MiA2LjA0NjIgMCAwIDAgLjc0MjcgNy4wOTY2IDUuOTggNS45OCAwIDAgMCAuNTExIDQuOTEwNyA2LjA1MSA2LjA1MSAwIDAgMCA2LjUxNDYgMi45MDAxQTUuOTg0NyA1Ljk4NDcgMCAwIDAgMTMuMjU5OSAyNGE2LjA1NTcgNi4wNTU3IDAgMCAwIDUuNzcxOC00LjIwNTggNS45ODk0IDUuOTg5NCAwIDAgMCAzLjk5NzctMi45MDAxIDYuMDU1NyA2LjA1NTcgMCAwIDAtLjc0NzUtNy4wNzI5em0tOS4wMjIgMTIuNjA4MWE0LjQ3NTUgNC40NzU1IDAgMCAxLTIuODc2NC0xLjA0MDhsLjE0MTktLjA4MDQgNC43NzgzLTIuNzU4MmEuNzk0OC43OTQ4IDAgMCAwIC4zOTI3LS42ODEzdi02LjczNjlsMi4wMiAxLjE2ODZhLjA3MS4wNzEgMCAwIDEgLjAzOC4wNTJ2NS41ODI2YTQuNTA0IDQuNTA0IDAgMCAxLTQuNDk0NSA0LjQ5NDR6bS05LjY2MDctNC4xMjU0YTQuNDcwOCA0LjQ3MDggMCAwIDEtLjUzNDYtMy4wMTM3bC4xNDIuMDg1MiA0Ljc4MyAyLjc1ODJhLjc3MTIuNzcxMiAwIDAgMCAuNzgwNiAwbDUuODQyOC0zLjM2ODV2Mi4zMzI0YS4wODA0LjA4MDQgMCAwIDEtLjAzMzIuMDYxNUw5Ljc0IDE5Ljk1MDJhNC40OTkyIDQuNDk5MiAwIDAgMS02LjE0MDgtMS42NDY0ek0yLjM0MDggNy44OTU2YTQuNDg1IDQuNDg1IDAgMCAxIDIuMzY1NS0xLjk3MjhWMTEuNmEuNzY2NC43NjY0IDAgMCAwIC4zODc5LjY3NjVsNS44MTQ0IDMuMzU0My0yLjAyMDEgMS4xNjg1YS4wNzU3LjA3NTcgMCAwIDEtLjA3MSAwbC00LjgzMDMtMi43ODY1QTQuNTA0IDQuNTA0IDAgMCAxIDIuMzQwOCA3Ljg3MnptMTYuNTk2MyAzLjg1NThMMTMuMTAzOCA4LjM2NCAxNS4xMTkyIDcuMmEuMDc1Ny4wNzU3IDAgMCAxIC4wNzEgMGw0LjgzMDMgMi43OTEzYTQuNDk0NCA0LjQ5NDQgMCAwIDEtLjY3NjUgOC4xMDQydi01LjY3NzJhLjc5Ljc5IDAgMCAwLS40MDctLjY2N3ptMi4wMTA3LTMuMDIzMWwtLjE0Mi0uMDg1Mi00Ljc3MzUtMi43ODE4YS43NzU5Ljc3NTkgMCAwIDAtLjc4NTQgMEw5LjQwOSA5LjIyOTdWNi44OTc0YS4wNjYyLjA2NjIgMCAwIDEgLjAyODQtLjA2MTVsNC44MzAzLTIuNzg2NmE0LjQ5OTIgNC40OTkyIDAgMCAxIDYuNjgwMiA0LjY2ek04LjMwNjUgMTIuODYzbC0yLjAyLTEuMTYzOGEuMDgwNC4wODA0IDAgMCAxLS4wMzgtLjA1NjdWNi4wNzQyYTQuNDk5MiA0LjQ5OTIgMCAwIDEgNy4zNzU3LTMuNDUzN2wtLjE0Mi4wODA1TDguNzA0IDUuNDU5YS43OTQ4Ljc5NDggMCAwIDAtLjM5MjcuNjgxM3ptMS4wOTc2LTIuMzY1NGwyLjYwMi0xLjQ5OTggMi42MDY5IDEuNDk5OHYyLjk5OTRsLTIuNTk3NCAxLjQ5OTctMi42MDY3LTEuNDk5N1oiLz48L3N2Zz4%3D" alt="Codex"></a>
  <a href="#install-cursor"><img src="https://img.shields.io/badge/Cursor-3B3B3B?style=for-the-badge&logo=cursor&logoColor=white" alt="Cursor"></a>
  <a href="#install-gemini-cli"><img src="https://img.shields.io/badge/Gemini_CLI-1A73E8?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini CLI"></a>
  <a href="#install-github-copilot"><img src="https://img.shields.io/badge/GitHub_Copilot-24292F?style=for-the-badge&logo=githubcopilot&logoColor=white" alt="GitHub Copilot"></a>
  <a href="#install-opencode"><img src="https://img.shields.io/badge/OpenCode-4A4A4A?style=for-the-badge&logo=opencode&logoColor=white" alt="OpenCode"></a>
</p>

<a id="install-claude-code"></a>**Claude Code**, testé. Depuis votre terminal :

```bash
claude plugin marketplace add Aboudjem/10x && claude plugin install contextify@10x
```

Puis, dans votre dépôt, demandez un premier brouillon :

```text
/contextify:contextify init
```

<a id="install-codex"></a>**Codex**, testé :

```bash
npx skills add Aboudjem/contextify -g -a codex
```

<a id="install-cursor"></a>**Cursor**, installation testée :

```bash
npx skills add Aboudjem/contextify -g -a cursor
```

<a id="install-gemini-cli"></a>**Gemini CLI**, installation testée :

```bash
npx skills add Aboudjem/contextify -g -a gemini-cli
```

<a id="install-github-copilot"></a>**GitHub Copilot**, installation testée :

```bash
npx skills add Aboudjem/contextify -g -a github-copilot
```

<a id="install-opencode"></a>**OpenCode**, installation testée :

```bash
npx skills add Aboudjem/contextify -g -a opencode
```

Seulement ce projet : retirez `-g`. Un autre agent : trouvez son code `-a` dans [la configuration des éditeurs](../docs/editors.md).

Hors de Claude Code, il n'y a pas de préfixe `/contextify:`. Demandez en toutes lettres : "contextify init", "contextify update".

Il faut Git, Bash et Python 3.11 ou plus récent. Aucun paquet Python, aucun serveur MCP, aucun appel réseau dans les scripts.

## Fonctionnement

Vous supprimez une cible Makefile, renommez un script ou déplacez un test. Vos agents suivent toujours les anciennes instructions. Chaque essai raté coûte un tour. contextify vous montre d'abord l'ancienne ligne :

1. `init` lit votre dépôt et rédige `AGENTS.md`. Un agent distinct relit chaque ligne face à sa source.
2. Vous voyez le diff. contextify écrit les fichiers et un tampon, la liste de ce que cite chaque ligne.
3. La vérification de dérive compare le dépôt au tampon. Une dérive, c'est une ligne qui cite quelque chose de disparu.

![Preuves, brouillon, relecture, écriture, vérification](../assets/how-it-works.svg)

| Mode     | Ce qui se passe                                                                                          |
| -------- | -------------------------------------------------------------------------------------------------------- |
| `init`   | Lire le dépôt, rédiger les instructions, relire les preuves, montrer un diff, puis écrire et vérifier.   |
| `update` | Relire les preuves et réviser le bloc géré. Vos modifications hors du bloc sont conservées.              |
| `check`  | Comparer les preuves avec le tampon commité. Rien n'est écrit.                                           |
| `accept` | Rafraîchir le tampon quand les instructions sont toujours justes. Les lignes qui citent un élément disparu sont refusées. |

Ce qu'il écrit :

| Fichier                                     | Lecteur                                                        | Lignes                           |
| ------------------------------------------- | -------------------------------------------------------------- | -------------------------------- |
| `AGENTS.md`                                 | Codex, Cursor et les autres agents qui lisent cette convention | Cible 20, 40 ou 60 ; maximum 150 |
| `CLAUDE.md`                                 | Claude Code, via `@AGENTS.md`                                  | 4 par défaut                     |
| `GEMINI.md`                                 | Gemini CLI, via `@AGENTS.md`                                   | 3                                |
| `.cursor/rules/contextify.mdc`              | Cursor ; facultatif, car Cursor lit aussi `AGENTS.md`          | 9                                |
| `.github/copilot-instructions.md`           | GitHub Copilot                                                 | 4                                |
| `docs/context/architecture.md`              | Carte facultative des composants et du flux de données         | Maximum 120                      |
| `docs/context/workflows.md`                 | Étapes facultatives de build, de test et de release            | Maximum 120                      |
| `.contextify/evidence.json` et `stamp.json` | La vérification de dérive                                      | Dépend du dépôt                  |

Codex et Cursor lisent `AGENTS.md` tel quel. Seuls les agents que vous choisissez reçoivent un fichier de renvoi. Chaque ligne factuelle pointe vers un fichier source et une ligne.

La vérification de dérive sort avec 0 et n'affiche rien quand le dépôt est à jour. En cas de dérive, elle affiche l'avis ci-dessus et sort quand même avec 0. Elle ne réécrit jamais un fichier.

Codes de sortie, mesurés dans bash le 2026-11-17 avec la 0.3.3 :

| Mode                                           | À jour                 | Dérive               | Pas encore de tampon | Vérification cassée |
| ---------------------------------------------- | ---------------------- | -------------------- | -------------------- | ------------------- |
| simple, `--strict`, `--json`, `--hook <agent>` | 0, aucune sortie       | 0, l'avis            | 3, l'avis `init`     | 1                   |
| `--ci`                                         | 0, `contextify: fresh` | 0, l'avis            | 0, l'avis `init`     | 1                   |
| `--git`                                        | 0, aucune sortie       | 0, l'avis sur stderr | 0, l'avis sur stderr | 1                   |
| `--ci --strict`, `--git --strict`              | 0                      | 1                    | 1                    | 1                   |

L'avis fait au plus 12 lignes et 2 048 octets. `--json` l'affiche sur une seule ligne de JSON. `--strict` seul ne change jamais le code de sortie. Il compte seulement les affirmations non vérifiées comme une dérive.

Les vérifications Git sont facultatives. À la fin de `init`, le skill propose d'installer des vérifications `pre-commit` et `pre-push`. Depuis un clone de ce dépôt, vous pouvez aussi lancer :

```bash
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

Par défaut, elles avertissent et refusent de remplacer des hooks existants. Ajoutez `--strict` pour bloquer un commit ou un push en cas de dérive.

L'activation refuse quand un `core.hooksPath` global est défini, car il masquerait vos autres hooks. Appelez plutôt `ctx-check --git` depuis le gestionnaire de hooks que vous utilisez déjà.

Pour un job de CI qui échoue sur une dérive, générez le workflow en mode strict. Son étape lance `ctx-check --ci --strict`. Elle échoue aussi sans tampon et sur toute affirmation non vérifiée, même dans un dépôt sans autre dérive :

```bash
bash skills/contextify/scripts/install_hooks.sh --strict --targets github --yes /path/to/repo
```

[Hooks et CI](../docs/hooks.md).

### Lancer la vérification de dérive à la main

Elle n'affiche rien quand le dépôt est à jour. Lancez-la depuis la racine de votre dépôt.

Installé comme plugin :

```bash
sh "$(ls -d ~/.claude/plugins/cache/10x/contextify/*/ | sort -V | tail -1)skills/contextify/scripts/ctx-check"
```

Installé avec `npx skills add -g` (Codex, Cursor, Gemini CLI, Copilot et OpenCode utilisent `~/.agents/skills`) :

```bash
sh ~/.agents/skills/contextify/scripts/ctx-check
```

Pour une installation de skills dans Claude Code, le dossier est `~/.claude/skills/contextify`. Sans `-g`, le dossier est dans votre dépôt : `.agents/skills/contextify`. Ajoutez `--ci --strict` pour qu'une dérive sorte avec le code 1.

Installer le skill ne compte pas comme une dérive. La vérification ignore la copie de contextify dans tout dossier d'agent, ainsi que `skills-lock.json`. Les autres skills ajoutés dans le `.agents/skills` de votre dépôt comptent, comme un changement `tree#depth2`. Pour les ignorer, ajoutez cette ligne :

```bash
echo ".agents/" >> .gitignore
```

## Preuve

Une seule commande lance toutes les suites, le contrat du skill et la vérification de dérive de ce dépôt sur lui-même :

```bash
make test
```

Voici ce qu'elle a affiché le 2026-11-17 (une ligne de résumé par suite, dans l'ordre d'exécution) :

```text
tests/test_ctx_check.py        128/128 checks passed
tests/test_verify_claims.py     30/30 checks passed
tests/test_hooks.py             Ran 22 tests, OK
tests/test_regressions.py       Ran 25 tests, OK
tests/test_supporting_docs.py   Ran 16 tests, OK
tests/test_manifests.py        155/155 checks passed
evals/check_skill.py           114/114 checks passed
make dogfood                   PASS: ctx-check is fresh and silent
                               29 claims, 0 stale, 0 unverified
```

La CI lance le même `make test` à chaque push et pull request. Le `AGENTS.md` de ce dépôt a été écrit par contextify, donc la dernière étape échoue s'il devient périmé.

## Compatibilité

| Agent | Installation | Testé |
| --- | --- | --- |
| Claude Code | `claude plugin install contextify@10x` | 2026-11-17 : installation du plugin, puis une exécution complète de `init` ([journal](../examples/python-service-0.3.0/README.md)) |
| Codex | `npx skills add Aboudjem/contextify -g -a codex` | 2026-11-17 : installation du skill, puis Codex a lancé la vérification de dérive ([journal](../examples/python-service-0.3.0/codex-run-0.3.1.md)) |
| Cursor | `npx skills add Aboudjem/contextify -g -a cursor` | 2026-11-17 : installation seule, dans un dossier personnel vide. Le skill est arrivé dans `~/.agents/skills`. |
| Gemini CLI | `npx skills add Aboudjem/contextify -g -a gemini-cli` | 2026-11-17 : installation seule, dans un dossier personnel vide. Le skill est arrivé dans `~/.agents/skills`. |
| GitHub Copilot | `npx skills add Aboudjem/contextify -g -a github-copilot` | 2026-11-17 : installation seule, dans un dossier personnel vide. Le skill est arrivé dans `~/.agents/skills`. |
| OpenCode | `npx skills add Aboudjem/contextify -g -a opencode` | 2026-11-17 : installation seule, dans un dossier personnel vide. Le skill est arrivé dans `~/.agents/skills`. |

"Installation seule" veut dire que les fichiers ont été vérifiés, mais que cet agent n'a pas lancé le skill. Documentés, non testés aujourd'hui : Gemini CLI et Cursor lançant le skill (les deux CLI ont refusé la connexion sur la machine de test), GitHub Copilot, OpenCode, Windsurf, Zed, Continue.dev et Kimi Code CLI. Leur configuration est dans [la configuration des éditeurs](../docs/editors.md).

## FAQ

### Pourquoi AGENTS.md est la source, et pas CLAUDE.md ?

Codex, Cursor et Copilot lisent `AGENTS.md` directement. Claude Code et Gemini CLI reçoivent un fichier court qui l'importe. Les mêmes faits vivent donc à un seul endroit.

### La vérification de dérive appelle-t-elle un modèle ?

Non. C'est un script shell et Python. Il lit Git et les fichiers que le tampon désigne, puis compare des empreintes. Il dépense zéro token.

### Faut-il un modèle particulier ?

Non. La vérification n'utilise aucun modèle. La rédaction avec `init` utilise le modèle que votre agent utilise déjà.

### Va-t-il écraser ce que j'ai écrit à la main ?

Non. contextify ne possède que le bloc entre ses marqueurs. Le texte hors du bloc survit à chaque mise à jour. Une modification dans le bloc déclenche un conflit au lieu d'être perdue.

### Une commande vérifiée fonctionne-t-elle vraiment ?

Pas prouvé. Une commande vérifiée est une commande dont le script, la cible ou le fichier existe. contextify ne la lance pas. Ce sont vos tests qui disent si elle marche.

### Que fait accept ?

Il rafraîchit le tampon quand les preuves ont bougé mais que les instructions sont toujours justes. Il refuse tant qu'une commande citée a disparu, pour qu'une ligne cassée ne puisse pas passer.

Plus de réponses dans la [FAQ complète](../docs/faq.md).

## Limites

- Une commande résolue a été trouvée, pas exécutée. Les preuves du dépôt peuvent elles-mêmes être fausses.
- Le résolveur ne comprend pas toutes les expressions shell ni tous les systèmes de build. Les lignes qu'il ne peut pas vérifier sont marquées `unverified`.
- Zéro token, c'est le coût de la vérification elle-même. Quand votre agent la lance et trouve une dérive, l'avis (12 lignes au plus) entre dans le contexte de l'agent.
- Aucune étude ne montre que ces fichiers aident les agents à finir leurs tâches. Une [étude de l'ETH Zurich](https://arxiv.org/abs/2602.11988) n'a trouvé aucun gain général, et les coûts du modèle ont augmenté de plus de 20 %. Gardez seulement les lignes qui évitent une vraie erreur.
- D'autres skills installés à côté de contextify, dans `.agents/skills` ou un autre dossier d'agent, apparaissent comme une dérive de l'arborescence. Ajoutez `.agents/` (ou ce dossier) à `.gitignore` pour les ignorer.
- Un tampon écrit par la 0.3.1 ou avant, avec le skill déjà installé, liste `.agents/skills/`. Après la mise à jour, la vérification affiche une fois `Changed tree#depth2`. Lancez `accept` une fois.
- Vous écrivez un dépôt de plugin ? `claude plugin validate --strict` avertit sur un `CLAUDE.md` à la racine. Faites pointer `.claude/CLAUDE.md` vers `@../AGENTS.md` à la main, comme ce dépôt. Le rédacteur ne cible pas encore ce chemin.
- Confidentialité : les scripts ne font aucun appel réseau. La rédaction passe par votre propre agent de code et sa connexion habituelle.

Toutes les limites, avec leurs sources : [docs/limits.md](../docs/limits.md).

## En savoir plus

[Démarrage rapide](../docs/quickstart.md) · [Exemples complets](../examples/README.md) · [Configuration des éditeurs](../docs/editors.md) · [Comparaison](../docs/comparison.md) · [Décisions de conception](../docs/design/DECISIONS.md)

[Contribuer](../CONTRIBUTING.md) · [Sécurité](../SECURITY.md) · [Changelog](../CHANGELOG.md) · [Licence MIT](../LICENSE) · [Hub de plugins 10x](https://github.com/Aboudjem/10x)

Traduction réalisée avec l'aide d'un modèle. Elle peut avoir du retard sur la [version anglaise](../README.md), qui fait référence. Les documents liés restent en anglais.
