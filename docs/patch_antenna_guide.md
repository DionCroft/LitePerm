# Patch Antenna Sensors

LitePerm supports patch-antenna research through editable geometry profiles, multilayer stacks, and inverse-modelling tools.

## Geometry Inputs

- patch length
- patch width
- substrate height
- substrate permittivity
- feed position
- ground plane dimensions
- sensing region dimensions
- protective layer thickness

## Recommended Workflow

1. Save the patch geometry as a reusable profile.
2. Capture S11 for the baseline and material-loaded states.
3. Use `Material Properties` for first-look dielectric exploration.
4. Use `Inverse Modelling` for property estimation and sensitivity ranking.
5. Save the result in `Research Mode`.

## Research Notes

- Patch sensors are especially sensitive to geometry drift and material thickness assumptions.
- Keep fabrication dimensions and substrate details in the experiment metadata.
- Use the same geometry profile for every sweep in a study series.

## Model Scope

The current patch workflow is a research-oriented simplified model, not a full-wave replacement.
