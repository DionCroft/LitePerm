# Developer Documentation

## High-Level Architecture

LitePerm is organised as a modular RF sensing and modelling stack:

1. `liteperm.devices`
2. `liteperm.acquisition`
3. `liteperm.calibration`
4. `liteperm.plugins`
5. `liteperm.transform`
6. `liteperm.inverse`
7. `liteperm.database`
8. `liteperm.reports`
9. `liteperm.ai`
10. `liteperm.api`
11. `liteperm.visualisation`

## Extension Points

### Transformation plugins

- implement the `TransformationPlugin` interface
- place the plugin in a discoverable package
- LitePerm registers it automatically without hard-coded wiring

### Forward models and inverse solvers

- implement the shared contracts
- keep simulation, optimisation, and uncertainty steps independently testable
- return serialisable outputs so experiments can be reopened later

## Storage Model

- `ExperimentDatabase` stores measurements, spectra, metadata, inverse results, and digital twins in SQLite
- `Projects/` mirrors the SQLite record with files for raw data, processed data, plots, reports, and YAML snapshots
- `MaterialDatabase` seeds the reference library and supports user additions

## Useful Commands

```bash
pytest -q
mkdocs build --strict
uvicorn liteperm.api.app:create_api_app --factory
streamlit run app.py
```
