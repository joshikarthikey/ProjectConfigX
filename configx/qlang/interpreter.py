"""
ConfigXQL - Interpreter (v0.1)

Executes ConfigXQL AST nodes against a ConfigTree instance.
This is the semantic layer that connects the language to the engine.

Design principles:
- No parsing logic here
- No storage logic here
- Pure AST -> Engine mapping

Current Version Supports :

`GET` 
GetNode(path=["app", "ui", "theme"], safe=False)
→ tree.get("app.ui.theme")

`SAFE GET`
GetNode(path=[...], safe=True)
→ returns None if missing

`SET`
SetNode(path=["app", "ui", "theme"], value="dark")
→ tree.set("app.ui.theme", "dark")

`DELETE`

DeleteNode(path=[...])
→ tree.delete("app.ui.theme")

"""

from typing import Any

from configx.core.tree import ConfigTree
from configx.core.errors import ConfigPathNotFoundError
from configx.qlang.parser import ConfigXQLParser, GetNode, SetNode, DeleteNode


class ConfigXQLInterpreter:
    """
    Executes ConfigXQL AST nodes against a ConfigTree.
    """

    def __init__(self, tree: ConfigTree):
        self.tree = tree
        self._parser = ConfigXQLParser()

    def execute(self, query: str) -> Any:
        """
        Parse and execute a single ConfigXQL query.

        Returns:
            - value for GET
            - None for SET / DELETE
        """
        node = self._parser.parse(query)

        if isinstance(node, GetNode):
            return self._exec_get(node)

        if isinstance(node, SetNode):
            return self._exec_set(node)

        if isinstance(node, DeleteNode):
            return self._exec_delete(node)

        raise TypeError(f"Unsupported AST node: {type(node)}")
    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    def _exec_get(self, node: GetNode):
        path = ".".join(node.path)

        try:
            return self.tree.get(path)
        except ConfigPathNotFoundError:
            if node.safe:
                return None
            raise

    def _exec_set(self, node: SetNode):
        path = ".".join(node.path)
        return self.tree.set(path, node.value)

    def _exec_delete(self, node: DeleteNode):
        path = ".".join(node.path)
        retr = self.tree.delete(path)
        
        # Design-Choice : Choosing to keep DELETE idempotent/safe
         
        # if not retr:
        #  raise ConfigPathNotFoundError(path)
        
        return retr
