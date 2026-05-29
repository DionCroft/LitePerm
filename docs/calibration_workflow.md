# Calibration Workflow

Calibration is the most important step for reliable permittivity measurement in LitePerm.

The goal is to remove systematic measurement error before the software estimates material properties.

## Wizard Structure

LitePerm Phase 5 uses a guided calibration wizard with six stages:

1. Open
2. Short
3. Load
4. Reference Material 1
5. Reference Material 2
6. Save Calibration

## Open, Short, Load

These standards define the one-port calibration baseline used by the measurement pipeline.

### Open

Use the open condition recommended for your sensor or probe setup.

### Short

Use the short condition recommended for your sensor or probe setup.

### Load

Use the matched or nominal load condition that best represents the calibration fixture.

## Reference Materials

Reference materials help LitePerm score measurement plausibility and compare measured spectra against known materials later in the workflow.

Recommended pairings:

- Air + Water
- Air + Methanol
- PTFE + FR4
- Water + Ethanol

## Capture Options

For every wizard step you can:

- import a `.s1p` file
- import a CSV file
- capture directly from the connected LiteVNA

The same sweep settings should normally be used for all standards and the material under test.

## Saving the Calibration

When the OSL standards are present, LitePerm can save the profile as YAML. The saved profile includes:

- calibration name
- selected reference materials
- notes
- source metadata for captured or imported standards

## Good Calibration Practice

- Do not move the cable or probe more than necessary between standards.
- Keep connectors clean and consistent.
- Re-run calibration if the sweep range changes significantly.
- Re-run calibration after changing sensor geometry or fixture arrangement.
- Re-run calibration if the validation confidence drops unexpectedly.

## When to Recalibrate

Recalibrate when:

- you changed the sweep range
- the device was disconnected and reassembled
- the sensor was replaced
- the ambient conditions changed significantly
- the validation system reports poor confidence

## Related Guides

- [Permittivity Measurement Guide](permittivity_measurement_guide.md)
- [Reference Materials Guide](reference_materials_guide.md)
- [Measurement Validation](measurement_validation.md)
