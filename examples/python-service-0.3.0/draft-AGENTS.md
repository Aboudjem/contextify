## Commands
- Run: `make serve`
- Test: `make test`
- Single test module: `make test-health`, or from the repo root `python3 -m unittest tests.test_health`
- No install, build or lint command is declared; `pyproject.toml` lists no dependencies

## Architecture
- `service/__main__.py` calls `serve()` in `service/server.py`, which binds `HOST` and `PORT` from `service/config.py`
- `service/handler.py` answers GET on exactly `/health`, with the JSON from `service/health.py`; any other GET path returns 404

## Testing
- `tests/test_config.py` asserts `HOST` is `127.0.0.1` and `PORT` is `8000`; update it when changing `service/config.py`
