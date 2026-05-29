# API Documentation

LitePerm exposes a FastAPI service for automation, scripting, and future external integrations.

## Start the API

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

## Current Endpoint Groups

- `/experiments`
- `/materials`
- `/calibrations`
- `/geometries`
- `/sweeps`
- `/plugins`

## Intended Uses

- connect LitePerm to external lab tooling
- browse saved experiments programmatically
- integrate materials and geometry profiles into notebooks
- prepare future automation around sweeps and archive export
