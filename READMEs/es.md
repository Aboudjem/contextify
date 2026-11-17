<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/hero-light.svg">
  <img alt="contextify: one repository, one source of instructions, multiple coding agents" src="../assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](../LICENSE)

[English](../README.md) | [Français](fr.md) | Español | [日本語](ja.md) | [简体中文](zh-CN.md)

<!-- may-lag -->

**Explica a cada agente de código cómo funciona tu repositorio. Luego demuestra que sigue siendo cierto.**

contextify escribe un `AGENTS.md` corto a partir de los archivos que lee tu agente. Después, un script local te avisa cuando queda desactualizado.

## Instalación

En Claude Code, desde tu terminal:

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install contextify@10x
```

Luego, dentro de tu repositorio, pide un primer borrador:

```text
/contextify:contextify init
```

Para Codex, Cursor, Gemini CLI y otros agentes, instala el skill:

```bash
npx skills add Aboudjem/contextify
```

En esos agentes no existe el prefijo `/contextify:`. Pídelo con palabras: "contextify init", "contextify update".

Necesita Git, Bash y Python 3.11 o posterior. Sin paquetes de Python, sin servidor MCP, sin llamadas de red desde los scripts.

### Ejecutar la comprobación de deriva a mano

No imprime nada cuando el repositorio está al día. Ejecútala desde la raíz de tu repositorio.

Instalado como plugin:

```bash
sh "$(ls -d ~/.claude/plugins/cache/10x/contextify/*/ | sort -V | tail -1)skills/contextify/scripts/ctx-check"
```

Instalado con `npx skills add` (Codex, Cursor y la mayoría de los demás usan `.agents/skills`):

```bash
sh .agents/skills/contextify/scripts/ctx-check
```

En una instalación de skills de Claude Code, la carpeta es `.claude/skills/contextify`. Añade `--ci --strict` para que una deriva salga con código 1.

Instalar el skill no cuenta como deriva. La comprobación ignora la copia de contextify en cualquier carpeta de agente y `skills-lock.json`. Otros skills que añadas en `.agents/skills` sí cuentan, como un cambio `tree#depth2`. Para ignorarlos, añade esta línea:

```bash
echo ".agents/" >> .gitignore
```

### Informe de ejemplo

El 2026-11-17, contextify 0.3.0 escribió `AGENTS.md` para un pequeño servicio en Python. Después se borró el objetivo `test-health` de su `Makefile`. La versión 0.3.2 imprime esto para ese repositorio, sin gastar tokens:

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

Un repositorio al día no imprime nada. Los archivos y el sello de esa ejecución vienen con el ejemplo, así que puedes repetirla:

```bash
sh examples/python-service-0.3.0/replay.sh
```

[Ejecución completa, archivos y el cambio que la provocó](../examples/python-service-0.3.0/README.md).

## Cómo funciona

![Evidencia, borrador, revisión, escritura, comprobación](../assets/how-it-works.svg)

| Modo     | Qué ocurre                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| `init`   | Lee el repositorio, redacta instrucciones, revisa la evidencia, muestra un diff, luego escribe y comprueba. |
| `update` | Vuelve a leer la evidencia y revisa el bloque gestionado. Tus cambios fuera del bloque se conservan.        |
| `check`  | Compara la evidencia con el sello confirmado. No escribe nada.                                              |
| `accept` | Renueva el sello cuando las instrucciones siguen siendo correctas. Rechaza las afirmaciones muertas.        |

Qué escribe:

| Archivo                                    | Lector                                                  | Líneas                           |
| ------------------------------------------ | ------------------------------------------------------- | -------------------------------- |
| `AGENTS.md`                                | Codex, Cursor y otros agentes que leen esta convención  | Objetivo 20, 40 o 60; máximo 150 |
| `CLAUDE.md`                                | Claude Code, mediante `@AGENTS.md`                      | 4 por defecto                    |
| `GEMINI.md`                                | Gemini CLI, mediante `@AGENTS.md`                       | 3                                |
| `.cursor/rules/contextify.mdc`             | Cursor; opcional, porque Cursor también lee `AGENTS.md` | 9                                |
| `.github/copilot-instructions.md`          | GitHub Copilot                                          | 4                                |
| `docs/context/architecture.md`             | Mapa opcional de componentes y flujo de datos           | Máximo 120                       |
| `docs/context/workflows.md`                | Pasos opcionales de build, pruebas y publicación        | Máximo 120                       |
| `.contextify/evidence.json` y `stamp.json` | La comprobación de deriva                               | Depende del repositorio          |

Solo los destinos que elijas reciben un archivo puntero. Cada línea factual apunta a un archivo fuente y a una línea. Un agente distinto revisa el borrador antes de que contextify escriba nada.

La comprobación de deriva sale con 0 y sin salida cuando el repositorio está al día. Si hay deriva, imprime el aviso de arriba y aun así sale con 0. Nunca reescribe un archivo.

Códigos de salida, medidos en bash el 2026-11-17 con la 0.3.2:

| Modo                                           | Al día                 | Deriva                | Aún sin sello         | La comprobación falló |
| ---------------------------------------------- | ---------------------- | --------------------- | --------------------- | --------------------- |
| simple, `--strict`, `--json`, `--hook <agent>` | 0, sin salida          | 0, el aviso           | 3, el aviso de `init` | 1                     |
| `--ci`                                         | 0, `contextify: fresh` | 0, el aviso           | 0, el aviso de `init` | 1                     |
| `--git`                                        | 0, sin salida          | 0, el aviso en stderr | 0, el aviso en stderr | 1                     |
| `--ci --strict`, `--git --strict`              | 0                      | 1                     | 1                     | 1                     |

El aviso tiene como máximo 12 líneas y 2048 bytes. `--json` lo imprime en una sola línea de JSON. `--strict` por sí solo nunca cambia el código de salida. Solo cuenta las afirmaciones no verificadas como deriva.

Las comprobaciones de Git son opcionales. Al final de `init`, el skill ofrece instalar comprobaciones `pre-commit` y `pre-push`. Desde un clon de este repositorio también puedes ejecutar:

```bash
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

Por defecto avisan y se niegan a reemplazar hooks existentes. Añade `--strict` para bloquear un commit o un push si hay deriva.

La activación se niega cuando hay un `core.hooksPath` global, porque ocultaría tus otros hooks. En su lugar, llama a `ctx-check --git` desde el gestor de hooks que ya uses.

Para un job de CI que falle con la deriva, genera el workflow en modo estricto. Su paso ejecuta `ctx-check --ci --strict`. También falla sin sello y con cualquier afirmación no verificada, incluso en un repositorio sin otra deriva:

```bash
bash skills/contextify/scripts/install_hooks.sh --strict --targets github --yes /path/to/repo
```

[Hooks y CI](../docs/hooks.md).

## Prueba

Un solo comando ejecuta todas las suites, el contrato del skill y la comprobación de deriva de este repositorio sobre sí mismo:

```bash
make test
```

Esto imprimió el 2026-11-17 (una línea de resumen por suite, en orden de ejecución):

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

La CI ejecuta el mismo `make test` en cada push y pull request. El `AGENTS.md` de este repositorio lo escribió contextify, así que el último paso falla si alguna vez queda desactualizado.

## Compatibilidad

| Agente      | Instalación                            | Probado                                                                                                                                             |
| ----------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Code | `claude plugin install contextify@10x` | 2026-11-17: instalación del plugin y luego una ejecución completa de `init` ([registro](../examples/python-service-0.3.0/README.md))                |
| Codex       | `npx skills add Aboudjem/contextify`   | 2026-11-17: instalación del skill y luego Codex ejecutó la comprobación de deriva ([registro](../examples/python-service-0.3.0/codex-run-0.3.1.md)) |

Documentados, no probados hoy: Gemini CLI y Cursor (ambas CLI rechazaron el inicio de sesión en la máquina de prueba), GitHub Copilot, OpenCode, Windsurf, Zed, Continue.dev y Kimi Code CLI. Su configuración está en [configuración de editores](../docs/editors.md).

## FAQ

### ¿Por qué la fuente es AGENTS.md y no CLAUDE.md?

Codex, Cursor y Copilot leen `AGENTS.md` directamente. Claude Code y Gemini CLI reciben un archivo corto que lo importa. Así los mismos hechos viven en un solo lugar.

### ¿La comprobación de deriva llama a un modelo?

No. Es un script de shell y Python. Lee Git y los archivos que señala el sello, y luego compara hashes. Gasta cero tokens.

### ¿Sobrescribirá lo que escribí a mano?

No. contextify solo es dueño del bloque entre sus marcadores. El texto fuera del bloque sobrevive a cada actualización. Un cambio dentro del bloque genera un conflicto en vez de perderse.

### ¿Un comando verificado funciona de verdad?

No está demostrado. Un comando verificado es uno cuyo script, objetivo o archivo existe. contextify no lo ejecuta. Tus pruebas siguen decidiendo si funciona.

### ¿Qué hace accept?

Renueva el sello cuando la evidencia cambió pero las instrucciones siguen siendo correctas. Se niega mientras un comando citado esté muerto, para que una línea rota no pase sin más.

Más respuestas en la [FAQ completa](../docs/faq.md).

## Límites

- Un comando resuelto se encontró, no se ejecutó. La propia evidencia del repositorio puede estar mal.
- El resolvedor no entiende todas las expresiones de shell ni todos los sistemas de build. Las líneas que no puede comprobar se marcan como `unverified`.
- Un [estudio de ETH Zurich](https://arxiv.org/abs/2602.11988) no encontró una mejora general en el éxito de las tareas gracias a los archivos de contexto, y sí un aumento del coste de inferencia de más del 20 %. contextify no tiene una ventaja medida en el éxito de las tareas. Conserva solo las líneas que evitan un error concreto.
- Otros skills instalados junto a contextify, en `.agents/skills` u otra carpeta de agente, aparecen como deriva del árbol. Añade `.agents/` (o esa carpeta) a `.gitignore` para ignorarlos.
- Un sello escrito por la 0.3.1 o anterior, con el skill ya instalado, incluye `.agents/skills/`. Tras la actualización, la comprobación muestra una vez `Changed tree#depth2`. Ejecuta `accept` una vez.
- ¿Escribes un repositorio de plugin? `claude plugin validate --strict` avisa de un `CLAUDE.md` en la raíz. Haz que `.claude/CLAUDE.md` apunte a `@../AGENTS.md` a mano, como este repositorio. El escritor todavía no apunta a esa ruta.
- Privacidad: los scripts no hacen llamadas de red. La redacción usa tu propio agente de código y su conexión habitual.

Todos los límites, con fuentes: [docs/limits.md](../docs/limits.md).

## Más información

[Inicio rápido](../docs/quickstart.md) · [Ejemplos completos](../examples/README.md) · [Configuración de editores](../docs/editors.md) · [Comparación](../docs/comparison.md) · [Decisiones de diseño](../docs/design/DECISIONS.md)

[Contribuir](../CONTRIBUTING.md) · [Seguridad](../SECURITY.md) · [Changelog](../CHANGELOG.md) · [Licencia MIT](../LICENSE) · [Hub de plugins 10x](https://github.com/Aboudjem/10x)

Traducción asistida por un modelo. Puede ir por detrás de la [versión inglesa](../README.md), que es la referencia. Los documentos enlazados están en inglés.
