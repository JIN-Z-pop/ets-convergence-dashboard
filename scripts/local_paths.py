"""local_paths.py — loader for machine-local file paths that are not tracked in this repo.

Resolution order:
  1. ETS_LOCAL_PATHS environment variable (path to a JSON file), if set.
  2. Default: ~/.ets-convergence/local_paths.json (outside the repo working tree).

The resolved config path must NOT be a file tracked in this git repository — that
guards against machine-local paths (usernames, local DB locations, etc.) ever being
committed into the public tree. See config/local_paths.example.json for the expected
keys and value shape.
"""
import json
import os
import subprocess
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".ets-convergence" / "local_paths.json"


def _repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent), check=True,
        ).stdout.strip()
        return Path(out).resolve()
    except Exception:
        return None


def _is_tracked(path, repo_root):
    if repo_root is None:
        return False
    try:
        rel = path.resolve().relative_to(repo_root)
    except ValueError:
        return False
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", str(rel)],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _resolve_config_path():
    env = os.environ.get("ETS_LOCAL_PATHS")
    path = Path(env).resolve() if env else DEFAULT_CONFIG_PATH.resolve()
    repo_root = _repo_root()
    if _is_tracked(path, repo_root):
        raise RuntimeError(
            f"ETS_LOCAL_PATHS resolved to a file tracked in this repo: {path}. "
            "This config must live outside version control. Point it at a "
            "machine-local, untracked file instead."
        )
    return path


def load():
    """Return the local paths config as a dict. Empty dict if the file does not exist."""
    path = _resolve_config_path()
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def require(key):
    """Return the path string for `key`, or raise a clear error if it is not configured."""
    config = load()
    if key not in config:
        path = _resolve_config_path()
        raise KeyError(
            f"local_paths key '{key}' is not set in {path}. "
            "See config/local_paths.example.json for the expected keys."
        )
    return config[key]
