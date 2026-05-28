# Calibration Guide

LitePerm currently implements a modular one-port Open/Short/Load workflow for S11 correction.

## Recommended Flow

1. Measure open, short, and load standards using the same frequency sweep as the DUT.
2. Import the DUT in `Raw Measurement`.
3. Import the three standards in `Calibration`.
4. Confirm the actual standard reflection coefficients if you use non-ideal standards.
5. Save the profile as YAML for reuse.

## Notes

- The profile YAML stores standard assumptions, reference material selections, and notes.
- The v0.1.0 calibration engine is intended as a transparent open-source baseline for research workflows.
- Reference-material support is included for future expansion toward multi-liquid or probe-specific calibration schemes.

