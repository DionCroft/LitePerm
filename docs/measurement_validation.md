# Measurement Validation

LitePerm Phase 5 adds a dedicated permittivity validation layer so the software does not stop at producing a spectrum. It also reports whether the result appears physically plausible and methodologically trustworthy.

## Validation Output

LitePerm reports:

- a confidence score
- a confidence label: Low, Medium, or High
- per-check diagnostic details

## Current Validation Checks

### Permittivity Range

Checks whether `epsilon'` and `epsilon''` stay inside broad practical dielectric bounds.

### Loss and Conductivity

Checks whether loss tangent and conductivity remain physically plausible for the measurement type.

### Noise Level

Uses the extracted spectrum and the S11 measurement to estimate whether the result looks excessively noisy.

### Frequency Stability

Checks whether the sweep axis is monotonic, dense enough, and wide enough to support interpretation.

### Calibration Quality

Rewards measurements that were made with a complete open-short-load calibration context.

### Reference Consistency

Rewards measurements that include reference material context for later comparison and traceability.

## How To Use the Score

### High

The result is a strong candidate for reporting, comparison, and archiving.

### Medium

The result is usable, but should be reviewed before being treated as a final research output.

### Low

The result probably needs a better sweep, fresh calibration, or stronger reference context.

## What Validation Does Not Replace

Validation is a quality aid. It does not replace:

- correct experimental design
- literature comparison
- repeated measurements
- sensor-domain expertise

## Improving a Low Score

If LitePerm returns a low confidence score:

- re-run the OSL calibration
- verify the selected sensor geometry
- increase sweep quality or point count
- reduce movement in the cable or fixture
- add or confirm reference materials
- repeat the measurement

## Related Guides

- [Permittivity Measurement Guide](permittivity_measurement_guide.md)
- [Calibration Workflow](calibration_workflow.md)
- [Reference Materials Guide](reference_materials_guide.md)
