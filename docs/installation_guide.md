# Installation Guide

## Requirements

- Python 3.12+
- Windows, Linux, or WSL2

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Linux or WSL2:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The sample Touchstone and CSV files in `examples/` are ready for a quick smoke test.

## Optional Services

API:

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

Hardware:

- Install `pyserial` through `requirements.txt` for direct LiteVNA USB serial support.
- Use the simulated live device backend if hardware is not currently attached.

