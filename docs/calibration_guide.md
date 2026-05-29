# Calibration Guide

LitePerm uses a modular one-port Open/Short/Load workflow for S11 correction and profile reuse.

## What You Need

- DUT measurement
- open standard
- short standard
- load standard
- the same frequency sweep for all four captures

## Recommended Flow

1. Measure open, short, load, and DUT using identical sweep settings.
2. Import the DUT in `Raw Measurement`.
3. Import the standards in `Calibration`.
4. Confirm the assumed standard reflection coefficients if you use non-ideal fixtures.
5. Save the calibration profile as YAML.
6. Apply the calibration when computing dielectric properties.

## Stored in the Calibration Profile

- open, short, and load reflection assumptions
- reference material names
- operator notes
- reusable YAML metadata

## Good Practice

- keep cable routing unchanged between standard and DUT measurements
- avoid changing start or stop frequency mid-calibration
- name profiles after the fixture and date
- save reference notes for future publications
