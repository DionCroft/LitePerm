# Developer Guide

## Architecture

LitePerm is organised as a modular S-parameter processing pipeline:

1. `liteperm.devices`
2. `liteperm.acquisition`
3. `liteperm.calibration`
4. `liteperm.plugins`
5. `liteperm.transform`
6. `liteperm.database`
7. `liteperm.reports`
8. `liteperm.ai`
9. `liteperm.api`
10. `liteperm.visualisation`

## Extending the inversion engine

- Add a new plugin module under `liteperm/plugins/builtin/` or a future plugin package.
- Implement the `TransformationPlugin` interface.
- The discovery manager will pick it up automatically.

## Live acquisition

- Device classes implement a common `DeviceBase` contract.
- `AcquisitionPipeline` keeps hardware capture, calibration, and transform stages separately testable.
- The `FutureDevice` backend exists to validate UI and database workflows without hardware.

## Research storage

- `ExperimentDatabase` stores metadata and serialised measurement payloads in SQLite.
- A matching on-disk project archive is created for raw data, processed data, plots, reports, and YAML metadata.
- `MaterialDatabase` seeds the built-in dielectric library and accepts user additions.

## Testing

```bash
pytest --cov=liteperm --cov-report=term-missing
```

## API

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

## Future roadmap

- Live LiteVNA acquisition
- Batch processing
- Material comparison mode
- ML-backed material classification and anomaly detection

