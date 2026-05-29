# Development Guide

Use this page when you are actively changing LitePerm rather than just consuming it.

## Recommended Local Loop

1. create a virtual environment
2. install `requirements.txt`
3. install `requirements-docs.txt`
4. run `pytest -q`
5. launch `streamlit run app.py`
6. build docs with `mkdocs build --strict`

## Before Opening a Pull Request

- run tests
- build docs
- check that the browser demo still loads
- update screenshots or placeholders if user-facing layout changes

Start with:

- [Developer Documentation](developer_guide.md)
- [Architecture](architecture.md)
- [API Documentation](api_guide.md)
- [Research Mode Guide](research_mode_guide.md)
