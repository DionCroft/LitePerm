# LitePerm

<p align="center">
  <img src="docs/images/liteperm_logo.svg" alt="LitePerm Logo" width="360"/>
</p>

<p align="center">
<b>Open-Source RF Sensing, Dielectric Spectroscopy and Inverse Electromagnetic Modelling Platform</b>
</p>

<p align="center">
Material Characterisation • RF Sensors • Patch Antennas • OECP • Biomedical Sensing • Digital Twins • AI-Ready Research Framework
</p>

---

# Overview

LitePerm is an open-source research platform designed to transform low-cost RF measurement hardware such as the LiteVNA 64 into a powerful dielectric spectroscopy, RF sensing, and inverse electromagnetic modelling system.

The project originated from the need for an accessible and extensible framework capable of converting measured S11 reflection data into meaningful material properties including:

* Complex Permittivity
* Conductivity
* Loss Tangent
* Material Thickness
* Dielectric Spectra
* Resonant Behaviour

Unlike traditional VNA software, LitePerm is designed not only to visualise measurements but also to estimate unknown material properties through forward and inverse electromagnetic modelling.

## Full-Wave Simulation

LitePerm now includes a modular Phase 4 full-wave solver layer designed to support simulation-assisted RF sensing workflows without locking the project to a single external tool.

Current Phase 4 support includes:

* `liteperm/solvers` integration package
* `SimulationJob` and `SimulationResult` models
* Solver registry and environment checks
* openEMS adapter scaffold
* Meep adapter scaffold
* Simulation caching under `Projects/<ProjectName>/simulations/`
* Measured versus simulated S11 comparison
* Full-wave forward-model support inside inverse modelling

Key Phase 4 documentation:

* `docs/full_wave_solver_guide.md`
* `docs/openems_setup_guide.md`
* `docs/meep_setup_guide.md`
* `docs/simulation_workflow.md`
* `CHANGELOG.md`

## Website and Documentation

- GitHub Pages documentation portal: `https://dioncroft.github.io/LitePerm/`
- Browser demo: `https://dioncroft.github.io/LitePerm/web_demo/`
- Repository: `https://github.com/DionCroft/LitePerm`

The platform provides a foundation for research in:

* Dielectric Spectroscopy
* Microwave Material Characterisation
* Patch Antenna Sensors
* Open Ended Coaxial Probe Measurements
* Biomedical RF Sensors
* Implantable Wireless Sensors
* Moisture Sensing
* Chemical Sensing
* Metamaterial Sensors
* AI-Assisted RF Classification
* Electromagnetic Digital Twins

---

# Why LitePerm?

Modern dielectric spectroscopy software is often:

* Proprietary
* Expensive
* Hardware-specific
* Difficult to extend
* Focused on industrial VNAs

LitePerm aims to provide an open, transparent and extensible alternative that can be used by:

* Researchers
* Students
* Engineers
* Startups
* Academic laboratories
* Maker communities

while leveraging affordable hardware such as the LiteVNA 64.

The long-term vision is to create a complete RF sensing ecosystem capable of linking:

```text
Measurement
      ↓
Calibration
      ↓
Electromagnetic Modelling
      ↓
Inverse Solvers
      ↓
Material Properties
      ↓
Digital Twin
      ↓
AI Classification
```

---

# Key Features

## RF Measurement

* Import Touchstone (.s1p) files
* Import LiteVNA CSV exports
* Live LiteVNA acquisition
* USB serial device support
* Frequency sweep management
* Measurement archiving

## RF Analysis

* S11 Magnitude
* S11 Phase
* Smith Charts
* Impedance Analysis
* Admittance Analysis
* Resonance Detection
* Q-Factor Analysis

## Dielectric Spectroscopy

* Complex Permittivity Extraction
* Dielectric Constant Analysis
* Loss Tangent Calculation
* Conductivity Estimation
* Frequency Dependent Material Characterisation

## Transformation Models

Currently supported:

* Stuchly
* Marsland
* Komarov

Plugin architecture allows future models to be added without modifying the core software.

## Sensor Support

LitePerm is designed to support multiple RF sensing modalities.

### Open Ended Coaxial Probe (OECP)

Traditional dielectric spectroscopy measurements.

### Patch Antenna Sensors

Resonant sensing structures for:

* Moisture
* Chemical
* Biological
* Biomedical applications

### Microstrip Resonators

High sensitivity dielectric sensors.

### Metamaterial Sensors

Future support for:

* CSRR
* DGS
* Metasurface structures

---

# Inverse Electromagnetic Modelling

One of LitePerm's primary goals is to estimate unknown material properties from measured RF responses.

Traditional workflow:

```text
Known Material
      ↓
Simulation
      ↓
Predicted S11
```

LitePerm enables:

```text
Measured S11
      ↓
Forward Model
      ↓
Optimisation Engine
      ↓
Estimated Material Properties
```

Target outputs include:

* Relative Permittivity (ε')
* Dielectric Loss (ε'')
* Conductivity (σ)
* Loss Tangent (tanδ)
* Material Thickness

---

# Digital Twin Framework

LitePerm introduces the concept of a measurement-linked digital twin.

Each experiment can maintain a virtual representation of:

* Sensor Geometry
* Calibration State
* Material Properties
* Environmental Conditions
* Measurement History

allowing future integration with:

* HFSS
* CST Studio
* COMSOL
* openEMS
* Meep

---

# Research Mode

LitePerm includes a dedicated research management framework.

Each experiment can store:

* Project Information
* Sensor Configuration
* Calibration Profiles
* Environmental Conditions
* Raw Measurements
* Processed Results
* Generated Reports

Experiments are archived automatically using a structured project hierarchy.

---

# Architecture

```text
LitePerm
│
├── Acquisition Layer
│
├── Calibration Engine
│
├── Transformation Engine
│
├── Sensor Models
│
├── Forward Models
│
├── Inverse Solvers
│
├── Uncertainty Analysis
│
├── Visualisation Layer
│
├── Research Database
│
├── Digital Twin Engine
│
└── API Layer
```

---

# Repository Structure

```text
LitePerm/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
│
├── docs/
├── examples/
├── profiles/
├── Projects/
├── tests/
│
└── liteperm/
    │
    ├── acquisition/
    ├── ai/
    ├── api/
    ├── calibration/
    ├── database/
    ├── devices/
    ├── geometry/
    ├── inverse/
    ├── io/
    ├── models/
    ├── plugins/
    ├── reports/
    ├── sensors/
    ├── synthetic/
    ├── transform/
    ├── uncertainty/
    ├── utils/
    └── visualisation/
```

---

# Installation

## Recommended Beginner Pages

If you are completely new to Git, GitHub, Python, or LitePerm, start with:

* `docs/installation_windows_11.md`
* `docs/quick_install_5_minutes.md`
* `docs/first_litevna_measurement_tutorial.md`

## LitePerm Installation Guide (Windows 11)

### Overview

This guide takes you from a completely new Windows 11 setup to a working LitePerm environment capable of:

* Loading LiteVNA Touchstone (`.s1p`) files
* Importing LiteVNA CSV exports
* Performing dielectric spectroscopy analysis
* Running inverse electromagnetic modelling
* Using Research Mode
* Accessing the LitePerm dashboard locally

Estimated setup time:

`15-30 minutes`

### Step 1 - Create a GitHub Account

If you do not already have a GitHub account:

1. Visit `https://github.com`
2. Click `Sign Up`
3. Follow the registration process
4. Verify your email address
5. Log into GitHub

### Step 2 - Install Git

LitePerm is distributed using Git.

Download Git for Windows:

`https://git-scm.com/download/win`

Installation:

1. Run the downloaded installer
2. Accept the default settings
3. Click `Next`
4. Click `Install`
5. Finish installation

Verify Git installation:

Open PowerShell and run:

```powershell
git --version
```

Expected output:

```text
git version 2.x.x
```

### Step 3 - Install Python

LitePerm currently targets:

`Python 3.12.x`

Download Python:

`https://www.python.org/downloads/`

Important:

When the installer appears, tick:

`Add Python to PATH`

before clicking `Install Now`.

Verify Python installation:

```powershell
python --version
pip --version
```

Expected output:

```text
Python 3.12.x
pip xx.x
```

### Step 4 - Install Visual Studio Code (Recommended)

Download:

`https://code.visualstudio.com/`

Install using default settings.

VS Code is strongly recommended for:

* Viewing code
* Editing files
* Using Git
* Running terminals

### Step 5 - Download LitePerm

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

### Step 6 - Create Python Virtual Environment

Create a virtual environment:

```powershell
python -m venv .venv
```

This creates an isolated Python environment inside:

```text
LitePerm
`-- .venv
```

### Step 7 - Activate Virtual Environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

Expected result:

```text
(.venv) PS C:\Projects\LitePerm>
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 8 - Install LitePerm Dependencies

Install all required packages:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This may take several minutes.

### Step 9 - Verify Installation

Run:

```powershell
pip list
```

You should see packages such as:

* `streamlit`
* `numpy`
* `scipy`
* `pandas`
* `plotly`
* `scikit-rf`
* `fastapi`
* `uvicorn`

### Step 10 - Launch LitePerm

Start the dashboard:

```powershell
streamlit run app.py
```

After a few seconds, a local URL similar to this should appear:

```text
http://localhost:8501
```

Open that address in your browser.

### Step 11 - Load Example Data

Use one of the included datasets:

* `examples/sample_touchstone.s1p`
* `examples/sample_litevna.csv`

Verify:

* S11 plot loads
* Smith chart appears
* Permittivity plots render

### Step 12 - Launch API (Optional)

LitePerm includes a FastAPI backend.

Start it with:

```powershell
uvicorn liteperm.api.app:create_api_app --factory
```

Default API URL:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

### Step 13 - Connecting a LiteVNA

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
   * Windows version
   * Python version
   * LitePerm version
   * Error message
   * Screenshot if possible

This greatly speeds up troubleshooting.

---

# Optional API Server

Start the FastAPI backend:

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

---

# Dashboard Modules

Current dashboard includes:

1. Raw Measurement
2. Live Measurement
3. Calibration
4. Sensor Geometry
5. Material Properties
6. Full-Wave Simulation
7. Inverse Modelling
8. Advanced Modelling
9. Research Mode
10. Experiment Explorer
11. Material Database

---

# Reference Materials

Built-in reference library includes:

* Air
* Water
* Methanol
* Ethanol
* Acetone
* NaCl Solutions
* Saline
* FR4
* PTFE
* Rogers 5880

Users may extend the material database with custom entries.

---

# Roadmap

## Phase 1

Core dielectric spectroscopy platform.

✅ Complete

## Phase 2

Research platform and experiment management.

✅ Complete

## Phase 3

Inverse electromagnetic modelling.

✅ Complete

## Phase 4

Full-wave solver integration.

Implemented:

* openEMS adapter scaffold
* Meep adapter scaffold
* Solver registry
* `SimulationJob` model
* `SimulationResult` model
* Simulation caching
* Measured versus simulated comparison

## Phase 5

Physics-informed machine learning.

Planned:

* Surrogate Models
* PINNs
* Material Classification

## Phase 6

Digital Twin Synchronisation.

Planned.

---

# Contributing

Contributions are welcome.

Areas of interest include:

* Electromagnetic Modelling
* RF Sensors
* Biomedical Sensors
* Dielectric Spectroscopy
* Material Characterisation
* AI for RF Systems
* Streamlit Development
* Scientific Visualisation

Please see:

* CONTRIBUTING.md
* ROADMAP.md

for further details.

---

# Citation

If you use LitePerm in academic work, please cite:

```text
Mariyanayagam, D.
LitePerm: Open-Source RF Sensing and Inverse Electromagnetic
Modelling Platform.
GitHub Repository:
https://github.com/DionCroft/LitePerm
```

---

# License

Released under the MIT License.

---

# Author

**Dr Dion M. Mariyanayagam**

Principal Lecturer in Electronics and Embedded Systems Engineering

London Metropolitan University

Research Interests:

* RF Sensors
* Embedded Systems
* Biomedical Engineering
* Microwave Sensing
* Artificial Intelligence
* Electromagnetic Material Characterisation
