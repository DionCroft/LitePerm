from liteperm.plugins.manager import discover_plugins, get_runnable_plugins


def test_plugin_discovery_includes_builtins_and_placeholders():
    plugins = discover_plugins()
    assert "stuchly" in plugins
    assert "marsland" in plugins
    assert "komarov" in plugins
    assert "patch_sensor" in plugins


def test_runnable_plugins_exclude_placeholders():
    runnable = get_runnable_plugins()
    assert "stuchly" in runnable
    assert "patch_sensor" not in runnable

