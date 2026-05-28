# LitePerm

LitePerm is an open-source Streamlit dashboard for LiteVNA-based dielectric spectroscopy and RF sensing. It imports S11 measurements from Touchstone or CSV exports, visualises raw RF behaviour, applies one-port calibration, and converts the reflection coefficient into frequency-dependent complex permittivity.

## Highlights

- Import `.s1p` and CSV S11 measurements from LiteVNA workflows
- Plot S11 magnitude, phase, and Smith chart
- Convert `S11 -> impedance -> admittance -> permittivity`
- Store calibration and geometry profiles as YAML
- Explore Stuchly, Marsland, and Komarov-style modelling interfaces
- Export dielectric spectra to CSV and Plotly figures to PNG/SVG
- Includes reference materials, example datasets, docs, and tests

## Scientific scope

LitePerm v0.1.0 focuses on a transparent, publishable, and extensible open-source research baseline. The inversion methods included in this version are intentionally modular and functional, but the Marsland and Komarov options are experimental placeholders rather than validated literature-identical implementations. They are suitable for architecture development, comparative prototyping, and method extension, not for unqualified metrology claims.

## Repository layout

```text
LitePerm/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── docs/
├── examples/
├── liteperm/
│   ├── io/
│   ├── calibration/
│   ├── transform/
│   ├── visualisation/
│   ├── models/
│   ├── geometry/
│   └── utils/
└── tests/
```

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Use `examples/sample_touchstone.s1p` or `examples/sample_litevna.csv` for a first run.

## Dashboard tabs

1. Raw Measurement
2. Calibration
3. Sensor Geometry
4. Material Properties
5. Advanced Modelling

## Reference materials

Built-in references live in `liteperm/reference_materials.yaml`:

- Air
- Water
- Methanol
- Ethanol
- Acetone
- NaCl Solution
- FR4
- PTFE
- Rogers 5880

## Documentation

- [Installation Guide](docs/installation_guide.md)
- [Calibration Guide](docs/calibration_guide.md)
- [Patch Antenna Guide](docs/patch_antenna_guide.md)
- [OECP Guide](docs/oecp_guide.md)
- [Developer Guide](docs/developer_guide.md)
- [Architecture Diagram](docs/architecture.md)

## Testing

```bash
pytest --cov=liteperm --cov-report=term-missing
```

## License

MIT

