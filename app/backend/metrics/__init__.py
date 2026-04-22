"""Metric package.

Importing this package triggers registration of every metric module.
Developers add a new metric by dropping a file in `local/` or `historical/`
and decorating the class with `@register_local` or `@register_historical`.
No central list to edit.
"""

import importlib
import pkgutil
from pathlib import Path


def _autoload(subpackage: str) -> None:
    pkg_path = Path(__file__).parent / subpackage
    for mod in pkgutil.iter_modules([str(pkg_path)]):
        if mod.name.startswith("_"):
            continue
        importlib.import_module(f"{__name__}.{subpackage}.{mod.name}")


_autoload("local")
_autoload("historical")
