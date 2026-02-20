from importlib.metadata import PackageNotFoundError, version as package_version

__all__ = ["__version__"]

try:
    __version__ = package_version("albion-command-desk")
except PackageNotFoundError:
    __version__ = "local-dev"
