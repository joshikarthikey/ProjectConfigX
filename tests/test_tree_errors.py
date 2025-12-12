# tests/test_tree_errors.py
import pytest

from configx.core.tree import ConfigTree
from configx.core.errors import (
    ConfigPathNotFoundError,
    ConfigStrictModeError,
    ConfigNodeStructureError,
    ConfigInvalidPathError,
)

def test_get_missing_path_raises():
    t = ConfigTree()
    with pytest.raises(ConfigPathNotFoundError):
        t.get("missing.path")

def test_invalid_path_error():
    t = ConfigTree()
    with pytest.raises(ConfigInvalidPathError):
        t.get("")

def test_strict_mode_blocks_auto_creation():
    t = ConfigTree(strict_mode=True)
    with pytest.raises(ConfigStrictModeError):
        t.set("a.b.c", 5)

def test_setting_value_on_interior_node_raises():
    t = ConfigTree()
    # create an interior node
    t.set("a.b.c", 5)
    # now "a.b" is interior
    with pytest.raises(ConfigNodeStructureError):
        t.set("a.b", 10)

def test_delete_root():
    t = ConfigTree()
    with pytest.raises(ConfigNodeStructureError):
        t.delete("root")
