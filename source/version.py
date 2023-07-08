from importlib import metadata

# Gets read from `pyproject.toml`
VERSION = metadata.metadata("miniircd-peerchat")["Version"]
