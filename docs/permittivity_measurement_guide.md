# Permittivity Measurement Guide

LitePerm is designed around one primary outcome:

> Measure complex permittivity from LiteVNA S11 data.

The recommended workflow is:

1. Connect LiteVNA.
2. Select the sensor or probe.
3. Run the calibration wizard.
4. Measure the material under test.
5. Review `epsilon'`, `epsilon''`, loss tangent, conductivity, and confidence.
6. Save the experiment.

## Before You Start

Prepare these items before launching LitePerm:

- LiteVNA connected by USB
- the probe or resonant sensor you intend to use
- open, short, and load standards
- at least one or two known reference materials
- the material under test

LitePerm works best when the sweep range and the sensor type are chosen before calibration.

## Basic Mode Workflow

Basic Mode is the fastest path to a result and hides RF details that are not essential for routine permittivity work.

### 1. Connect LiteVNA

Open `Connect LiteVNA` and:

- detect the COM port
- connect the device
- test communication
- set start frequency, stop frequency, point count, output power, and sweep speed

### 2. Run the Calibration Wizard

Open `Calibration Wizard` and complete:

1. Open
2. Short
3. Load
4. Reference Material 1
5. Reference Material 2
6. Save Calibration

You can either import each standard from file or capture it directly from the connected LiteVNA.

### 3. Configure the Sensor

Open `Sensor Setup` and choose:

- Open Ended Coax Probe
- Patch Sensor
- Microstrip Resonator
- Custom Sensor

Then confirm the geometry values before moving on.

### 4. Measure the Material

Open `Measure Material` and either:

- capture the measurement from LiteVNA
- import a Touchstone `.s1p` file
- import a LiteVNA CSV export

Press `Calculate Permittivity` once the material sweep is loaded.

### 5. Review the Result

Open `Permittivity Results` to inspect:

- frequency-dependent `epsilon'`
- frequency-dependent `epsilon''`
- loss tangent
- conductivity
- validation score
- closest matching materials from the reference database

## Advanced Mode

Advanced Mode adds:

- S11 magnitude and phase
- Smith chart
- impedance and admittance
- live capture tools
- inverse modelling
- full-wave simulation
- plugin inspection

Use Advanced Mode when you want to debug the measurement chain or perform deeper modelling.

## What LitePerm Uses Internally

LitePerm still performs the full RF transform chain internally:

`S11 -> calibration -> impedance -> admittance -> permittivity`

In Basic Mode, LitePerm keeps those intermediate RF views out of the way so the result is instrument-like and easier to use routinely.

## Best Practices

- Keep the probe and cable arrangement stable between calibration and material measurement.
- Use at least two reference materials whenever possible.
- Choose a frequency range that matches the sensing structure.
- Save the experiment immediately after a successful measurement.
- Review the validation confidence before treating the result as publication-ready.

## Next Guides

- [Calibration Workflow](calibration_workflow.md)
- [Probe Setup Guide](probe_setup_guide.md)
- [Reference Materials Guide](reference_materials_guide.md)
- [Measurement Validation](measurement_validation.md)
