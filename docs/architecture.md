# Architecture

![LitePerm architecture diagram](images/architecture-diagram.svg)

```mermaid
flowchart LR
    A[LiteVNA Device or File Import] --> B[Raw Measurement]
    B --> C[Calibration Engine]
    C --> D[Network Transform]
    D --> E[Transformation Plugin]
    E --> F[Dielectric Spectrum]
    F --> G[Inverse Modelling]
    F --> H[Plotly Dashboard]
    F --> I[SQLite Experiment Store]
    F --> J[Project Archive]
    G --> K[Digital Twin]
    I --> L[Experiment Explorer]
    I --> M[AI Dataset Builder]
    I --> N[FastAPI Service]
    H --> O[GitHub Pages Documentation]
```

## Design Principles

- modular processing stages
- independently testable capture and modelling layers
- reproducible experiment storage
- research-friendly export formats
- scalable path toward future EM solver integration
