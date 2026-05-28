"""Dynamic discovery for transformation plugins."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from functools import lru_cache

from liteperm.plugins import builtin
from liteperm.plugins.base import TransformationPlugin


SKIP_MODULES = {"base", "manager"}


def _load_plugin_modules() -> None:
    for module_info in pkgutil.walk_packages(builtin.__path__, prefix=f"{builtin.__name__}."):
        if module_info.name.rsplit(".", 1)[-1] in SKIP_MODULES:
            continue
        importlib.import_module(module_info.name)


def _walk_plugin_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _walk_plugin_subclasses(subclass)


@lru_cache(maxsize=1)
def discover_plugins() -> dict[str, TransformationPlugin]:
    _load_plugin_modules()
    plugins: dict[str, TransformationPlugin] = {}
    for plugin_class in _walk_plugin_subclasses(TransformationPlugin):
        if inspect.isabstract(plugin_class):
            continue
        plugin = plugin_class()
        plugins[plugin.name().lower()] = plugin
    return dict(sorted(plugins.items()))


def get_plugin(name: str) -> TransformationPlugin:
    plugins = discover_plugins()
    key = name.lower()
    if key not in plugins:
        raise KeyError(f"Unknown transformation plugin: {name}")
    return plugins[key]


def get_runnable_plugins() -> dict[str, TransformationPlugin]:
    return {name: plugin for name, plugin in discover_plugins().items() if plugin.metadata().get("implemented", True)}
