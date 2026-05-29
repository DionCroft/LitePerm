# Installation Guide

LitePerm supports Windows, Linux, and WSL2. The fastest route is:

1. install Python 3.12+
2. install Git
3. clone the repository
4. create a virtual environment
5. install dependencies
6. launch Streamlit

## Choose Your Platform

| Platform | Guide |
| --- | --- |
| Windows 11 | [Windows 11 Installation](installation_windows_11.md) |
| Ubuntu | [Ubuntu Installation](installation_ubuntu.md) |
| WSL2 | [WSL2 Installation](installation_wsl2.md) |

## Core Commands

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### Ubuntu / WSL2

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Optional Components

FastAPI service:

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

Documentation tooling:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## Verification

After installation, confirm that:

- `streamlit run app.py` opens a browser page
- `examples/sample_touchstone.s1p` imports successfully
- the Smith chart renders
- one experiment can be saved

## Common Errors

- Python not on PATH
- PowerShell activation blocked
- missing `python3-venv` on Ubuntu
- serial permission issues on Linux
- `kaleido` missing when exporting figures

For a complete first-session walkthrough, continue to [Quick Start](QuickStart.md).
