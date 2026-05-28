# Developer Guide

## Architecture

LitePerm is organised as a modular S-parameter processing pipeline:

1. `liteperm.io`
2. `liteperm.calibration`
3. `liteperm.transform`
4. `liteperm.models`
5. `liteperm.visualisation`

## Extending the inversion engine

- Add a new method class to `liteperm/models/permittivity_methods.py`
- Register it in `METHOD_REGISTRY`
- The Streamlit app will pick it up automatically through `available_methods()`

## Testing

```bash
pytest --cov=liteperm --cov-report=term-missing
```

## Future roadmap

- Live LiteVNA acquisition
- Batch processing
- Material comparison mode
- ML-backed material classification and anomaly detection

