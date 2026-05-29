# Ubuntu Installation

This path is recommended for lab workstations, Linux laptops, and remote analysis machines.

## 1. Install System Packages

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

Verify:

```bash
python3 --version
git --version
```

## 2. Clone the Repository

```bash
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
```

## 3. Create and Activate a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional docs tooling:

```bash
pip install -r requirements-docs.txt
```

## 5. Run LitePerm

```bash
streamlit run app.py
```

Optional API service:

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

## 6. Verify

1. Open the local Streamlit URL shown in the terminal.
2. Load one of the example files.
3. Check that the `Material Properties` plots render.
4. Save an experiment to confirm database and archive creation.

## Troubleshooting

### `python3-venv` is missing

Install it explicitly:

```bash
sudo apt install python3-venv
```

### Serial port permissions

If LiteVNA access is denied, add your user to the `dialout` group and sign out:

```bash
sudo usermod -aG dialout "$USER"
```

### Browser does not open automatically

Copy the Streamlit URL from the terminal into Firefox or Chromium manually.

## Screenshot Placeholder

![Ubuntu installation placeholder](images/live-acquisition-view.svg)
