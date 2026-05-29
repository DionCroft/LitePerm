# Windows 11 Installation

This guide is written for first-time users who want LitePerm running with as little friction as possible.

## 1. Install Python

Download Python 3.12 or newer from the official Python website and enable **Add Python to PATH** during setup.

Verify:

```powershell
python --version
pip --version
```

## 2. Install Git

Install Git for Windows from the official Git website.

Verify:

```powershell
git --version
```

## 3. Clone the Repository

```powershell
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
```

## 4. Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 5. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Optional documentation dependencies:

```powershell
pip install -r requirements-docs.txt
```

## 6. Launch LitePerm

Streamlit dashboard:

```powershell
streamlit run app.py
```

FastAPI service:

```powershell
uvicorn liteperm.api.app:create_api_app --factory
```

## 7. Verify the Installation

Use these checks:

- Open the Streamlit dashboard in your browser
- Load `examples/sample_touchstone.s1p`
- Confirm the Smith chart and material plots render
- Save one experiment in `Research Mode`

## Troubleshooting

### `python` is not recognised

Reinstall Python and make sure PATH integration is enabled.

### PowerShell blocks activation

Use the `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` command shown above.

### Plot export fails

Make sure `kaleido` is installed from `requirements.txt`.

### LiteVNA does not connect

- Confirm the COM port in Device Manager
- Close any other software already using the port
- Try the simulated device backend first to confirm the app is healthy

## Screenshot Placeholder

![Windows installation placeholder](images/dashboard-overview.svg)
