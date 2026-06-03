"""Lazy loading utilities to speed up application startup."""

import sys
from importlib import import_module

_module_cache = {}


def lazy_import(module_name, attribute=None):
    """Lazily import a module or attribute on first access."""
    if module_name not in _module_cache:
        mod = import_module(module_name)
        _module_cache[module_name] = mod
    
    module = _module_cache[module_name]
    if attribute:
        return getattr(module, attribute)
    return module
