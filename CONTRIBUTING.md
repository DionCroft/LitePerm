# Contributing

LitePerm is intended to support long-term collaborative RF sensing research.

## Workflow

1. Create a focused branch.
2. Add or update tests with each behavior change.
3. Run `python -m pytest -q`.
4. Run `ruff check .`.
5. Keep docs and example workflows aligned with code changes.

## Pull Requests

- Explain the sensing or architecture problem being solved.
- Note whether the change affects acquisition, calibration, modelling, storage, or UI.
- Include screenshots for Streamlit UI changes when practical.
- Call out any assumptions made for hardware protocols or inverse models.

## Review Priorities

- Measurement integrity
- Calibration safety
- Backwards compatibility
- Test coverage
- Documentation clarity

