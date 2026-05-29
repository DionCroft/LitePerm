# OECP Sensors

The open-ended coaxial probe workflow is the cleanest match for the current transform and inverse interfaces.

## Geometry Inputs

- inner radius
- outer radius
- flange radius
- cable permittivity

## Recommended Flow

1. Save the probe geometry profile.
2. Perform OSL calibration with the same sweep settings as the DUT.
3. Import the measurement.
4. Compute dielectric properties with the Stuchly baseline first.
5. Compare with alternative plugins or the inverse engine if needed.

## Method Notes

- `Stuchly` is the most direct baseline
- `Marsland` is exposed as an experimental broadband correction path
- `Komarov` is exposed as an experimental dispersive correction path
