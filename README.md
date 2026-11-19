# QC-GIS Playwright

End-to-end tests for the GreenSpace–LST console written by Justin Rivera

## This uses pytest-playwright and it runs with `uv`.

## Run

1. Start the console in the GIS repo (`npm run dev` or `npm run build && npm run start`). The
   database does not need to be running: see "Data" below.
2. Here, once:

   ```bash
   uv sync
   uv run playwright install chromium
   ```

3. Run the suite:

   ```bash
   uv run pytest
   ```

   Another copy of the console: `uv run pytest --base-url http://127.0.0.1:3100`.
   One file or one test: `uv run pytest tests/issues/test_issue_104_opacity_zero.py -k stacked`.
   Watch it: add `--headed --slowmo 300`. Traces for failures: add `--tracing retain-on-failure`.

   After every run a **"What was tested"** table lists each test grouped by area (UI, then
   GitHub issues) and feature, with what it checked, PASS / FAIL / SKIP and its time
   (`tests/summary.py`). A test's docstring, when it has one, becomes its description.

## Data

The console's database is still experimental, so the tests do not depend on it. The `api`
fixture (`tests/conftest.py`) answers every `/api` read from the data files the GIS repo ships
(`public/data`), which are what the API serves. Writes are refused in this mode.

- `QC_DATA_DIR=...` points at those files if the GIS repo is not next to this one.
- `QC_API=live` lets requests reach the real API and database instead; that is where upload and
  delete tests will go once the database settles.

## Layout

```text
tests/
├── conftest.py   fixtures: browser defaults, the api mock, page errors, offline, the console
├── pages/        page objects: console, compare, about
├── ui/           behaviour: navigation, map lock, side panels, selection and hover details
└── issues/       one file per GitHub issue: test_issue_<number>_<slug>.py
```

A failing test's file says which feature or issue broke.
