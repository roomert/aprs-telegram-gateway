# Building standalone executables

All build settings live in **`build.toml`**: the executable name, the entry
script, the extra `.py` files and packages to bundle, data files, and runtime
dependencies. Edit that file. You normally never touch the other build files.

| File | What it does |
|---|---|
| `build.toml` | **Your settings**, the only file you edit |
| `build.py` | Shared logic that reads `build.toml` and runs PyInstaller |
| `build.sh` | Linux / Raspberry Pi wrapper: makes `.venv`, then runs `build.py` |
| `build.ps1` | Windows wrapper: same thing |

Output goes to `dist/` as one file, e.g. `aprs-tg-bot-windows-x64.exe`,
`aprs-tg-bot-linux-x64`, `aprs-tg-bot-linux-arm64`.

Requires **Python 3.11+** (Raspberry Pi OS Bookworm ships 3.11).

## Adding script files

PyInstaller follows ordinary `import` statements from the entry script on its
own. List your modules under `[sources] files` anyway, because that also
catches modules loaded dynamically:

```toml
[sources]
files = ["aprs_client.py", "backends"]   # a folder needs an __init__.py
```

## Windows x64

```powershell
.\build.ps1
.\build.ps1 -Label windows-x64-test     # custom label
```

If scripts are blocked: `powershell -ExecutionPolicy Bypass -File .\build.ps1`

## Linux x64 and ARM64 (Raspberry Pi)

```sh
sh ./build.sh
sh ./build.sh --label debian12-arm64    # custom label
```

PyInstaller **cannot cross-compile**. Build each executable on its target:
the Windows exe on Windows, linux-x64 on an x64 Linux box (or WSL), and
linux-arm64 on a 64-bit Pi OS. Build on the oldest glibc / OS you want to
support, because executables built on newer systems may not run on older ones.

## Data files at runtime

Files listed under `[data]` are unpacked to a temp folder when the program runs:

```python
import os, sys
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE, "aliases.example.json")
```

Settings the user changes, like a bot token or alias list, should sit **next to**
the executable rather than inside it: `os.path.dirname(sys.executable)`.
