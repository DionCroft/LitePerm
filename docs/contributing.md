# Contributing

LitePerm is structured so researchers and engineers can contribute in small, reviewable pieces.

## Good First Contributions

- improve documentation pages
- add screenshots from real measurements
- contribute additional example datasets
- refine calibration notes
- add new transformation plugins
- improve forward models or inverse solvers

## Local Setup for Contributors

```bash
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-docs.txt
```

## Useful Commands

Run the dashboard:

```bash
streamlit run app.py
```

Run the API:

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

Run tests:

```bash
pytest -q
```

Build docs:

```bash
mkdocs build --strict
```

Serve docs locally:

```bash
mkdocs serve
```

## Pull Request Expectations

- keep features modular
- include tests when behaviour changes
- update docs when user-facing workflows change
- avoid breaking saved experiment formats without a migration path

For repository-wide collaboration details, also read the root `CONTRIBUTING.md`.
