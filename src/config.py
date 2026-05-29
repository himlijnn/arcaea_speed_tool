"""Load config.toml — resolves relative paths against the current working directory."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_config(config_path: str = "config.toml") -> dict:
    """Read and parse config.toml, return a configuration dictionary.

    Relative paths are resolved against the current working directory,
    so the tool works both in development and when installed as a wheel.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = Path.cwd() / config_path

    with open(path, "rb") as f:
        return tomllib.load(f)
