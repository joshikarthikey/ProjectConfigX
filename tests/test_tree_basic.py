# tests/test_tree_basic.py
from configx.core.tree import ConfigTree

def test_set_and_get_leaf():
    t = ConfigTree()
    t.set("app.ui.theme", "dark")
    assert t.get("app.ui.theme") == "dark"

def test_get_interior_returns_dict():
    t = ConfigTree()
    t.set("app.ui.theme", "dark")
    t.set("app.ui.accent", "blue")

    data = t.get("app.ui")
    assert data == {"theme": "dark", "accent": "blue"}

def test_delete_leaf():
    t = ConfigTree()
    t.set("app.ui.theme", "dark")
    t.delete("app.ui.theme")

    assert t.get("app.ui") == {}  # no children left

def test_to_dict():
    t = ConfigTree()
    t.set("a.b.c", 10)
    assert t.to_dict() == {"a": {"b": {"c": 10}}}

def test_load_dict():
    t = ConfigTree()
    t.load_dict({"app": {"title": "MyApp"}})
    assert t.get("app.title") == "MyApp"
