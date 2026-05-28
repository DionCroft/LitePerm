# Open-Ended Coax Probe Guide

The OECP workflow is the most direct match for the current Stuchly, Marsland, and Komarov-style inversion interfaces.

## Geometry Inputs

- `Inner Radius`
- `Outer Radius`
- `Flange Radius`
- `Cable Permittivity`

## Method Notes

- `Stuchly` provides the simplest baseline inversion.
- `Marsland` adds an experimental broadband fringing correction.
- `Komarov` adds an experimental dispersive correction layer.

These methods are intentionally separated behind a registry so you can replace or extend them with literature-grade implementations later.

