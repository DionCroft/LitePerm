# Reference Materials Guide

LitePerm includes a built-in reference material library for permittivity comparison and measurement validation.

## Built-In Materials

The bundled database includes:

- Air
- Water
- Methanol
- Ethanol
- Acetone
- NaCl Solution
- Saline
- FR4
- PTFE
- Rogers 5880

## Why Reference Materials Matter

Reference materials improve the measurement workflow in three ways:

1. They give calibration context.
2. They let LitePerm compare measured spectra against known materials.
3. They support unknown-material identification using nearest-neighbour style matching.

## What LitePerm Stores

Each material entry can include:

- material name
- category
- known permittivity
- known conductivity
- frequency range
- source or literature reference
- notes

## Choosing Reference Materials

Choose reference materials that are relevant to the measurement problem.

Examples:

- liquid sensing: Water, Methanol, Ethanol
- PCB and substrate sensing: FR4, PTFE, Rogers 5880
- saline or biomedical work: Saline, NaCl Solution

## Comparison Mode

After a measurement, LitePerm can compare the measured dielectric spectrum against the material library and report:

- similarity score
- difference in `epsilon'`
- difference in `epsilon''`
- difference in conductivity

This is useful for quick screening and sanity checks.

## Adding Custom Materials

Use the Material Database tools in Advanced Mode to add your own entries.

Recommended minimum fields:

- material name
- category
- `epsilon'`
- `epsilon''`
- conductivity
- source
- notes

## Notes on Accuracy

Reference values are only as good as the source data and the frequency range they represent. Treat them as comparative anchors, not universal truths across every possible sensor, solvent purity, temperature, or concentration.

## Related Guides

- [Permittivity Measurement Guide](permittivity_measurement_guide.md)
- [Calibration Workflow](calibration_workflow.md)
- [Measurement Validation](measurement_validation.md)
