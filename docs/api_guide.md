# API Guide

LitePerm exposes a FastAPI service for integration with external tools.

## Start

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

## Endpoints

- `/experiments`
- `/materials`
- `/calibrations`
- `/geometries`
- `/sweeps`
- `/plugins`

The API layer is intentionally thin in Phase 2 so it can evolve alongside the database and acquisition services.

