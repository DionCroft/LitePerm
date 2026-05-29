# LitePerm Installation Guide (Windows 11)

## Overview

This guide takes you from a completely new Windows 11 installation to a fully working LitePerm environment capable of:

- loading LiteVNA Touchstone (`.s1p`) files
- importing LiteVNA CSV exports
- performing dielectric spectroscopy analysis
- running inverse electromagnetic modelling
- using Research Mode
- accessing the LitePerm dashboard locally

Estimated setup time:

`15-30 minutes`

## Step 1 - Create a GitHub Account

If you do not already have a GitHub account:

1. Visit `https://github.com`
2. Click `Sign Up`
3. Follow the registration process
4. Verify your email address
5. Log into GitHub

## Step 2 - Install Git

LitePerm is distributed using Git.

Download Git for Windows:

`https://git-scm.com/download/win`

### Installation

1. Run the downloaded installer
2. Accept the default settings
3. Click `Next`
4. Click `Install`
5. Finish installation

### Verify Git Installation

Open PowerShell and run:

```powershell
git --version
```

Expected output:

```text
git version 2.x.x
```

## Step 3 - Install Python

LitePerm currently targets:

`Python 3.12.x`

Download Python:

`https://www.python.org/downloads/`

### Important

When the installer appears, tick:

`Add Python to PATH`

before clicking `Install Now`.

This is critical.

### Verify Python Installation

Open PowerShell and run:

```powershell
python --version
pip --version
```

Expected output:

```text
Python 3.12.x
pip xx.x
```

## Step 4 - Install Visual Studio Code (Recommended)

Download:

`https://code.visualstudio.com/`

Install using default settings.

VS Code is strongly recommended for:

- viewing code
- editing files
- using Git
- running terminals

## Step 5 - Download LitePerm

Create a working directory. Example:

```text
C:\Projects
```

Open PowerShell and run:

```powershell
cd C:\Projects
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
```

## Step 6 - Create Python Virtual Environment

Create a virtual environment:

```powershell
python -m venv .venv
```

This creates:

```text
LitePerm
`-- .venv
```

which contains an isolated Python environment.

## Step 7 - Activate Virtual Environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

Expected result:

```text
(.venv) PS C:\Projects\LitePerm>
```

The `(.venv)` prefix indicates activation succeeded.

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Step 8 - Install LitePerm Dependencies

Install all required packages:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This may take several minutes.

## Step 9 - Verify Installation

Run:

```powershell
pip list
```

You should see packages such as:

- `streamlit`
- `numpy`
- `scipy`
- `pandas`
- `plotly`
- `scikit-rf`
- `fastapi`
- `uvicorn`

## Step 10 - Launch LitePerm

Start the dashboard:

```powershell
streamlit run app.py
```

After a few seconds, a local URL similar to this should appear:

```text
http://localhost:8501
```

Open that address in your browser.

## Step 11 - Load Example Data

Use one of the included datasets:

- `examples/sample_touchstone.s1p`
- `examples/sample_litevna.csv`

Verify:

- the S11 plot loads
- the Smith chart appears
- the permittivity plots render

## Step 12 - Launch API (Optional)

LitePerm includes a FastAPI backend.

Start it with:

```powershell
uvicorn liteperm.api.app:create_api_app --factory
```

Default API URL:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Step 13 - Connecting a LiteVNA

1. Connect the LiteVNA via USB
2. Open `Device Manager`
3. Expand `Ports (COM & LPT)`
4. Note the device COM port, for example `USB Serial Device (COM5)`
5. In LitePerm, open `Live Measurement`
6. Select the COM port and connect

## Updating LitePerm

Navigate to the project:

```powershell
cd C:\Projects\LitePerm
.\.venv\Scripts\Activate.ps1
git pull
pip install -r requirements.txt
```

## Closing LitePerm

Stop Streamlit:

```text
CTRL + C
```

Deactivate the environment:

```powershell
deactivate
```

## Common Problems

### Python Not Found

Error:

```text
python is not recognised
```

Solution:

Reinstall Python and ensure `Add Python to PATH` is checked.

### Git Not Found

Error:

```text
git is not recognised
```

Solution:

Reinstall Git for Windows.

### Streamlit Not Found

Error:

```text
streamlit is not recognised
```

Solution:

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Port 8501 Already In Use

Launch Streamlit on a different port:

```powershell
streamlit run app.py --server.port 8502
```

## Updating to New Releases

To update to the latest release:

```powershell
git pull
pip install -r requirements.txt
```

To switch to a specific release:

```powershell
git checkout v0.3.0
```

## Repository

LitePerm GitHub repository:

`https://github.com/DionCroft/LitePerm`

## Support

If you encounter issues:

1. Check existing GitHub Issues
2. Create a new GitHub Issue
3. Include:
   - Windows version
   - Python version
   - LitePerm version
   - Error message
   - Screenshot if possible

This greatly speeds up troubleshooting.

## Related Pages

- [Quick Install (5 Minutes)](quick_install_5_minutes.md)
- [First LiteVNA Measurement Tutorial](first_litevna_measurement_tutorial.md)
