# Setup

> The pipeline produces **predicted** attention from DeepGaze IIE. It is not real eye-tracking.

The pipeline runs on the CPU; no graphics card is needed. On macOS it takes about 2.5 GB of disk space (packages plus model); expect more on Linux and Windows, where the packages are larger. The first install takes a few minutes. It has been run on macOS only so far; the Linux and Windows steps below follow the same script but have not been tried by the group yet.

## What you need

- **Python 3.13**
- **git**
- **`just`**, a small command runner that gives the commands short names
- `curl` (already present on macOS and most Linux systems)

## macOS

1. Install [Homebrew](https://brew.sh) if you do not have it.
2. In Terminal:
   ```bash
   brew install just python@3.13 git
   ```
3. Go to [Get the code and install](#get-the-code-and-install).

## Linux

1. Install Python 3.13 (with its `venv` module), git, curl and `just` with your package manager. On Ubuntu:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.13 python3.13-venv git curl
   ```
   The `add-apt-repository` line is only needed if your Ubuntu version does not ship Python 3.13.
2. Install `just`: on recent Ubuntu, `sudo apt install just`. For other systems see the [just installation page](https://github.com/casey/just#installation).
3. Go to [Get the code and install](#get-the-code-and-install).

## Windows

The setup script is written for macOS and Linux, so on Windows it runs inside WSL (Windows Subsystem for Linux), which gives you an Ubuntu terminal on Windows.

1. Open PowerShell as administrator and run:
   ```powershell
   wsl --install
   ```
   Restart when asked, then open **Ubuntu** from the Start menu and create a user name and password.
2. Inside the Ubuntu window, follow the [Linux](#linux) steps above.
3. Keep the project inside the Ubuntu home folder (for example `~/glancelab-deepgaze-attention`), not under `/mnt/c/`, which is much slower.
4. To look at the output images, type `explorer.exe .` in the project folder: it opens that folder in Windows Explorer.

Running it directly in PowerShell or Command Prompt, without WSL, is not supported.

## Get the code and install

```bash
git clone https://github.com/00017501/glancelab-deepgaze-attention.git
cd glancelab-deepgaze-attention
just setup
```

`just setup` creates a private Python environment in `.venv/`, installs the pinned packages, downloads DeepGaze at a fixed version, and fetches one small data file. It is safe to run again.

If your Python 3.13 has another name, pass it: `PYTHON=/path/to/python3.13 just setup`.

## Check that it works

```bash
just test     # a few seconds, no model
just demo     # the whole pipeline on the placeholder images
```

The first `just demo` downloads the model weights (about 1 GB), so it needs an internet connection and takes longer than later runs. When it finishes, open `examples/placeholder/output/PLACEHOLDER_panel.png`: you should see three placeholder versions side by side with a heatmap over each.

## If something goes wrong

| Problem | What to try |
|---|---|
| `just: command not found` | Install `just` (see your system above), then open a new terminal |
| `python3.13: command not found` | Install Python 3.13, or pass its location: `PYTHON=/path/to/python3.13 just setup` |
| `just setup` stops halfway | Run it again; it picks up where it can |
| A package fails to install on your system | The versions in `requirements.txt` were pinned on macOS. Tell the group which package failed |

## Without `just`

```bash
./setup.sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m src.glance_attention run --study examples/placeholder
```

Every `just` command is a short name for `.venv/bin/python -m src.glance_attention <command> --study <folder>`; the `justfile` lists them all.

Next: [using it on the real ads](ANALYSIS_GUIDE.md).
