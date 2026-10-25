"""Shared build logic. Reads build.toml and runs PyInstaller.

You normally don't edit this file - edit build.toml instead.
Run via build.sh / build.ps1, or directly:  python build.py [--label LABEL] [--config FILE]
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        sys.exit("Python 3.11+ is required (or 'pip install tomli' for older versions).")

ROOT = Path(__file__).resolve().parent


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def default_label() -> str:
    machine = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(machine, machine)
    if sys.platform.startswith("win"):
        return f"windows-{arch}"
    if sys.platform == "darwin":
        return f"macos-{arch}"
    return f"linux-{arch}"


def resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="build.toml", help="config file (default: build.toml)")
    ap.add_argument("--label", default=None, help="output label (default: auto, e.g. linux-arm64)")
    ap.add_argument("--skip-install", action="store_true", help="don't pip install dependencies")
    args = ap.parse_args()

    cfg_path = resolve(args.config)
    if not cfg_path.is_file():
        fail(f"Config not found: {cfg_path}")
    try:
        cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        fail(f"{cfg_path.name} has a syntax error: {e}")

    app = cfg.get("app", {})
    sources = cfg.get("sources", {})
    data = cfg.get("data", {})
    deps = cfg.get("dependencies", {}).get("packages", [])

    name = app.get("name", "app")
    label = args.label or default_label()
    for what, val in (("app.name", name), ("label", label)):
        if not re.fullmatch(r"[A-Za-z0-9._-]+", val):
            fail(f"{what} may contain only letters, numbers, dots, underscores and hyphens: {val!r}")

    entry = resolve(app.get("entry", ""))
    if not entry.is_file():
        fail(f"Entry script not found: {entry}")
    if entry.stat().st_size == 0:
        fail(f"Entry script is empty: {entry}. Add code before building.")

    exe_name = f"{name}-{label}"
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "--onefile",
           "--name", exe_name,
           "--distpath", str(ROOT / "dist"),
           "--workpath", str(ROOT / "build" / "pyinstaller"),
           "--specpath", str(ROOT / "build"),
           "--paths", str(ROOT)]

    cmd.append("--console" if app.get("console", True) else "--noconsole")
    if app.get("icon"):
        icon = resolve(app["icon"])
        if not icon.is_file():
            fail(f"Icon not found: {icon}")
        cmd += ["--icon", str(icon)]

    for sp in sources.get("search_paths", []):
        p = resolve(sp)
        if not p.is_dir():
            fail(f"search_paths entry is not a folder: {p}")
        cmd += ["--paths", str(p)]

    for f in sources.get("files", []):
        p = resolve(f)
        if p.is_file() and p.suffix == ".py":
            cmd += ["--paths", str(p.parent), "--hidden-import", p.stem]
        elif p.is_dir():
            if not (p / "__init__.py").is_file():
                fail(f"Package folder has no __init__.py: {p}")
            cmd += ["--paths", str(p.parent), "--collect-submodules", p.name]
        else:
            fail(f"sources.files entry not found (or not a .py file/package): {p}")

    for mod in sources.get("hidden_imports", []):
        cmd += ["--hidden-import", mod]

    for src, dest in data.items():
        p = resolve(src)
        if not p.exists():
            fail(f"Data file/folder not found: {p}")
        cmd += ["--add-data", f"{p}{os.pathsep}{dest}"]

    cmd.append(str(entry))

    if deps and not args.skip_install:
        print(f"Installing dependencies: {', '.join(deps)}")
        subprocess.run([sys.executable, "-m", "pip", "install", *deps], check=True)

    print(f"Building {exe_name} ...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        fail("PyInstaller failed.")

    suffix = ".exe" if sys.platform.startswith("win") else ""
    print(f"Build complete: {ROOT / 'dist' / (exe_name + suffix)}")


if __name__ == "__main__":
    main()
