# Quick Install (5 Minutes)

This page is for users who want the shortest path to a working LitePerm dashboard on Windows 11.

## Goal

Get LitePerm installed, open the dashboard, and load a sample dataset in about five minutes.

## Prerequisites

Before starting, make sure you already have:

- Git installed
- Python 3.12 installed
- a GitHub account if you want to clone from GitHub directly

If not, use the full [Windows 11 Installation Guide](installation_windows_11.md).

## Commands

Open PowerShell and run:

```powershell
cd C:\Projects
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Expected Result

After a short wait, Streamlit should print a URL similar to:

```text
http://localhost:8501
```

Open it in your browser.

## First Checks

1. Go to `Raw Measurement`
2. Load `examples/sample_touchstone.s1p`
3. Confirm:
   - S11 magnitude is visible
   - the Smith chart renders
   - the app does not show import errors
4. Open `Material Properties`
5. Confirm the permittivity plots appear

## If It Fails

### `python` is not recognised

Reinstall Python and make sure `Add Python to PATH` is enabled.

### `git` is not recognised

Install Git for Windows and restart PowerShell.

### `streamlit` is not recognised

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then rerun:

```powershell
pip install -r requirements.txt
```

## Next Step

Once LitePerm is running, continue to the [First LiteVNA Measurement Tutorial](first_litevna_measurement_tutorial.md).
