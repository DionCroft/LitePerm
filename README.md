# LitePerm

<p align="center">
  <img src="docs/images/liteperm_logo.png" alt="LitePerm Logo" width="300"/>
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

## Windows

Clone the repository:

```bash
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate environment:

```bash
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch LitePerm:

```bash
streamlit run app.py
```

Deactivate environment:

```bash
deactivate
```

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
6. Inverse Modelling
7. Advanced Modelling
8. Research Mode
9. Experiment Explorer
10. Material Database

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

Planned:

* openEMS
* Meep

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
