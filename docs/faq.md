# FAQ

## Do I need a LiteVNA to use LitePerm?

No. You can start with Touchstone or CSV files, the browser demo, or the simulated live device backend.

## Can LitePerm run without Python?

The full application cannot, but the [Web Demo](web_demo.md) can visualise files in a browser without local Python installation.

## Is the browser demo research-grade?

No. It is for exploration, teaching, and quick previews. Use the full Streamlit application for calibration-aware research workflows.

## Where are experiments stored?

LitePerm stores them in SQLite plus a matching `Projects/Project_Name/Experiment_ID/` archive structure.

## Can I export publication figures?

Yes. The Streamlit application supports PNG, SVG, and PDF export for Plotly figures.

## Does LitePerm support inverse electromagnetic modelling?

Yes. Phase 3 introduced the inverse engine, and it is documented in the [Inverse Modelling Guide](inverse_modelling_guide.md).

## Can I connect to LiteVNA directly from the browser?

Not yet. See [Browser Connectivity](BrowserConnectivity.md) for the current feasibility assessment.

## How should I cite LitePerm?

Use the repository `CITATION.cff` file and the [Publications](publications.md) page.
