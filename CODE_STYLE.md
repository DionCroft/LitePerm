# Code Style Guide

- Target Python 3.12+.
- Prefer explicit, modular services over large multi-purpose functions.
- Keep numerical transforms pure and independently testable.
- Isolate hardware communication from the rest of the pipeline.
- Use YAML for human-edited profiles and SQLite for structured research records.
- Treat experimental RF models as clearly labelled until validated.
- Preserve backwards compatibility for public APIs unless a migration path is documented.

