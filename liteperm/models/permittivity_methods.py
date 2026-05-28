"""Backward-compatible view of the transformation plugin ecosystem."""

from __future__ import annotations

from liteperm.plugins.manager import discover_plugins, get_runnable_plugins


def method_registry(include_placeholders: bool = False):
    return discover_plugins() if include_placeholders else get_runnable_plugins()


METHOD_REGISTRY = method_registry()
