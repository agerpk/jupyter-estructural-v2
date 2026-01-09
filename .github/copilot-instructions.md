# Copilot / AI Agent Instructions for AGP (jupyter_estructural_v2)

## Quick context (read *before* editing)
- App is an MVC Dash app (see `app.py`): `models/` (data & state), `views/` + `components/` (UI), `controllers/` (callbacks & business logic).
- Core runtime: Dash + Flask, visualizations with Plotly. Persistent data lives in `data/` and cache in `data/cache`.
- **Authoritative rules:** `gemini.md` (project guide) and `.amazonq/rules/` (robot rules). Read them when unsure.

## High-priority rules for automated edits (Actionable)
1. Follow existing patterns—do not invent new architectures. When adding UI+logic, put UI in `views/` or `components/` and callbacks in `controllers/`.
2. Most controllers use a `register_callbacks(app)` function. Use that pattern (callers like `app.py` register all controllers). Avoid standalone `@callback` decorators unless there is an explicit precedent (search repo first).
3. App state is centralized in `models/app_state.py` (use `AppState()` to access persistence and managers like `estructura_manager`).
4. File-based persistence: JSON files are the source of truth (`data/*.estructura.json`, families `.familia.json`). Read the file at callback start (Dash State can be stale).
5. Caching: use `utils/calculo_cache.py` helpers. Cache filenames and hashes follow a strict naming pattern (e.g., `{name}.calculoCMC.json`, `CMC_{name}.{hash}.json`). Compute hashes with `CalculoCache.calcular_hash(...)` and include `nodos_editados` when relevant.
6. Plotly figures: when saving to cache **always** write both PNG and JSON (example: `fig.write_image()` and `fig.write_json()`), otherwise cached graphs won't render.
7. DataFrames: serialize with `df.to_json(orient='split')` and load with `pd.read_json(..., orient='split')` if you need to preserve layout/format.
8. No placeholders: never add fake implementations or hardcoded working data—raise `ValueError` or return `None` and clearly mark TODO in docs if a full implementation is out of scope (see `.amazonq/rules/never_placeholders.md`).
9. No hot reload: app disables hot reload on purpose. When testing changes: stop the server, run `python app.py`, then refresh the browser (see `.amazonq/rules/no_hot_reload.md` and `app.py`).
10. QA protocol: after implementing a fix mark the issue as `🔧 TESTING PENDIENTE` (do not mark as resolved; the owner will close it). See `.amazonq/rules/qa_testing_protocol.md`.
11. No ejecutar tests ni correr scripts: no ejecutar pruebas automatizadas ni lanzar scripts (por ejemplo, `pytest`, `python test_*.py`, o cualquier script de mantenimiento) en el entorno; el usuario es el responsable de ejecutar tests y scripts de la aplicación y de validar cambios en su entorno local.

## How to run & debug (practical commands)
- Start locally: `python app.py` (app config reads `config/app_config.py`). Hot reload is disabled in code.
- Quick import checks: run `python test_app.py` or `python test_simple.py` to sanity-check imports and layout creation.
- Deployment: see `README_DEPLOY.md`, `verify_deploy.py` and `RENDER_DEPLOYMENT_CHECKLIST.md`. Production uses Gunicorn (Procfile must expose `server` from `app.py`).

## Common pitfalls & troubleshooting checks
- Duplicate callbacks / DuplicateCallback errors: ensure component IDs are unique across the app, and use `allow_duplicate=True` only when needed.
- Stale State: re-load file-backed data at the top of callbacks instead of trusting `State` (see `gemini.md` "Stale State" note).
- Plotly not showing from cache: JSON file missing. Always write JSON when saving figures to cache.
- Unexpected callback triggers: use `dash.callback_context` and explicit `if n_clicks is None:` guards.

## Files & locations that are authoritative examples
- `app.py` — app bootstrap, `server = app.server`, disabled hot reload
- `controllers/*_controller.py` — preferred callback registration pattern (`register_callbacks(app)`)
- `utils/calculo_cache.py` — canonical cache API and filename/hash patterns
- `utils/estructura_manager.py` — structure save/load conventions
- `verify_deploy.py`, `README_DEPLOY.md`, `RENDER_DEPLOYMENT_CHECKLIST.md` — deployment checks and commands
- `gemini.md` and `.amazonq/rules/*` — policies and agent rules; read them before making behavior decisions

## Tone & communication for PRs from AI
- Keep PR descriptions factual and short. Link to relevant docs and tests that validate the change.
- If a change affects UX or data model, add or update a short doc in `/docs` and mention the migration steps.
- Add unit / integration checks (e.g., small script or `pytest` tests) for regressions when possible.

---
If you'd like, I can open a small PR adding this file and list which sections you'd prefer expanded (e.g., callback examples, cache format, or deploy checklist). Please tell me which area to expand next.