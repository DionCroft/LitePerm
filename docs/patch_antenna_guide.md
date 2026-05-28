# Patch Antenna Guide

Patch antenna sensors can be approximated in LitePerm through an effective capacitance model derived from the patch area and substrate height.

## Parameters

- `Length`
- `Width`
- `Substrate Height`
- `Substrate Permittivity`
- `Feed Offset`
- `Ground Plane Dimensions`

## Practical Advice

- Use the same geometry profile for all related sweeps in a study.
- Treat the current permittivity reconstruction as a first-order sensing model unless you have a validated inversion for your resonator.
- Export both the raw S11 and the dielectric spectrum when documenting experiments.

