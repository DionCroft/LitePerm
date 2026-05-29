# WSL2 Installation

WSL2 is a strong option if you want Linux tooling on Windows while still working on local LiteVNA datasets.

## 1. Install WSL2

From an elevated PowerShell window:

```powershell
wsl --install
```

Restart Windows when prompted and complete Ubuntu setup.

## 2. Install Prerequisites Inside WSL2

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

## 3. Clone and Install LitePerm

```bash
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run the Dashboard

```bash
streamlit run app.py
```

On modern WSL2 builds, the app is usually available from your Windows browser at the URL printed by Streamlit.

## 5. Run the API

```bash
uvicorn liteperm.api.app:create_api_app --factory
```

## Notes About LiteVNA Hardware

WSL2 works very well for file-based workflows. USB serial access to physical devices may require extra Windows-to-WSL forwarding depending on your setup.

If your goal is live capture:

- try Windows-native LitePerm first
- or use file export from LiteVNA desktop software into WSL2

## Troubleshooting

### Cannot reach Streamlit from Windows

Try launching with an explicit address:

```bash
streamlit run app.py --server.address 0.0.0.0
```

### USB device is visible in Windows but not WSL2

Use the Windows-native install path for live serial acquisition, or export `.s1p` and CSV files from Windows software and analyse them in WSL2.

## Screenshot Placeholder

![WSL2 installation placeholder](images/dashboard-overview.svg)
