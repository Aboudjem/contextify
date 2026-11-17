.PHONY: test dogfood

# One command for the whole suite. CI runs exactly this target.
test:
	python3 tests/test_ctx_check.py
	python3 tests/test_verify_claims.py
	python3 tests/test_hooks.py
	python3 tests/test_regressions.py
	python3 tests/test_supporting_docs.py
	python3 tests/test_manifests.py
	python3 evals/check_skill.py skills/contextify/SKILL.md
	$(MAKE) dogfood

# This repository runs contextify on itself: the check must be fresh and silent.
dogfood:
	@out=$$(sh skills/contextify/scripts/ctx-check); rc=$$?; \
	if [ "$$rc" -ne 0 ] || [ -n "$$out" ]; then echo "FAIL: ctx-check exit=$$rc output=[$$out]"; exit 1; fi; \
	echo "PASS: ctx-check is fresh and silent"
	python3 skills/contextify/scripts/verify_claims.py --strict --budget AGENTS.md docs/context/architecture.md docs/context/workflows.md
