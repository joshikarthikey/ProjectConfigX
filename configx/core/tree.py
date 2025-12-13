"""
configx.core.tree

Tree definition : The ConfigTree is the Manager of All Nodes
It has one job:

> Provide a clean, predictable interface to get/set/delete/query hierarchical parameters.

Refer rules.md for rules of a ConfigX Node.

Developed & Maintained by Aditya Gaur, 2025

"""


from __future__ import annotations
from typing import Any, Dict, List, Optional
import struct
import io
import os

from .node import Node
from .errors import (
    ConfigPathNotFoundError,
    ConfigInvalidPathError,
    ConfigStrictModeError,
    ConfigNodeStructureError,
    ConfigInvalidFormatError,
)


class ConfigTree:
    def __init__(self, strict_mode: bool = False):
        """
        Create a ConfigTree.

        :param strict_mode: when True, setting a deep path that has missing
                            intermediate nodes will raise an error instead
                            of auto-creating them.
        """
        # the root node holds the top-level children
        self.root: Node = Node(name="root")

        # runtime flag to enforce strict path creation behavior
        self.strict_mode: bool = strict_mode

    def _split(self, path: str) -> List[str]:
        """
        Normalize and split a dotted path into parts.
        Examples:
          "a.b.c" -> ["a","b","c"]
        """
        if path is None:
            raise ConfigInvalidPathError(str(path), "Path cannot be None.")

        
        parts = [p for p in path.strip().split(".") if p]

        if len(parts) == 0:
            raise ConfigInvalidPathError(path, "Path cannot be empty.")

        return parts

    def _walk(self, path: str, create_missing: bool = False):
        """
        Walk the tree and return the node at `path`.
        If create_missing is True, intermediate nodes are created as interior nodes.
        Returns None if a required node is missing and create_missing is False.
        """
        parts = self._split(path)
        node = self.root

        for idx, part in enumerate(parts):
            # Node exists → descend
            if part in node.children:
                node = node.children[part]
                continue

            # Node missing
            if create_missing:
                # Strict mode disallows creating missing nodes
                if self.strict_mode:
                    raise ConfigStrictModeError(path)

                # Create new interior node
                new_node = Node(name=part)
                node.children[part] = new_node
                node = new_node
                continue

            # Missing but not allowed to create
            return None

        return node

    
    def get(self, path: str) -> Any:
        """
        Return a primitive value for a leaf node or a dict for an interior node.
        Raises KeyError if path does not exist.
        """
        node = self._walk(path, create_missing=False)
        if node is None:
            raise ConfigPathNotFoundError(path)

        return node.to_primitive()
    

    def set(self, path: str, value: Any) -> Any:
        """
        Set a leaf value at `path`. Creates intermediate nodes if permitted.
        Enforces strict rule: a node that currently has children cannot be converted
        into a leaf (error), and a leaf with a value cannot become interior with children.
        Returns the assigned value.
        """
        parts = self._split(path)
        if not parts:
            raise ConfigInvalidPathError(path, "Empty path is not allowed.")

        # walk and create intermediates if allowed
        node = self._walk(path, create_missing=True)
        if node is None:
            raise ConfigPathNotFoundError(path)

        # strict rule: cannot assign to interior node
        if len(node.children) > 0:
            raise ConfigNodeStructureError(
                path,
                "Cannot assign value to an interior node; it has children."
            )

        # Safe to set: assign value and infer type
        node.value = value
        node.type = Node.infer_type(value)
        
        # ensure children remain empty for strictness (defensive)
        node.children = {}

        return node.value

    def delete(self, path: str) -> bool:
        """
        Delete the node at `path`. Returns True if deletion occurred, False if path not found.
        Deleting the root is forbidden.
        """
        parts = self._split(path)

        if len(parts) == 1 and parts[0] == "root":
            raise ConfigNodeStructureError(path, "Cannot delete root node.")

        parent_path = ".".join(parts[:-1])
        parent = self._walk(parent_path, create_missing=False) if parent_path else self.root

        if parent is None:
            return False

        key = parts[-1]

        if key not in parent.children:
            return False

        parent.children.pop(key)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entire tree into a nested Python dict of primitives.
        """
        return self.root.to_primitive() if self.root.children else {}

    def load_dict(self, data: Dict[str, Any]):
        """
        Replace the tree with nodes built from a Python dict.
        This is a destructive operation: it resets the existing tree.
        """
        if not isinstance(data, dict):
            raise ConfigInvalidFormatError("Top-level configuration must be a dict.")

        self.root = Node(name="root")

        for key, value in data.items():
            if not isinstance(key, str):
                raise ConfigInvalidFormatError("All keys must be strings.")

            self.root.children[key] = Node.from_primitive(key, value)

    def set_strict_mode(self, enabled: bool):
        """Allow toggling strict mode at runtime."""
        self.strict_mode = bool(enabled)

    # -------------------------------------------------------------------------
    # PERSISTENCE LAYER: Custom Binary Format
    # -------------------------------------------------------------------------

    def save_to_bin(self, file_path: str):
        """
        Saves the current state to a custom binary format (.cfgx).
        """
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'wb') as f:
            # 1. Write Header: Magic 'CFGX' + Version 0x01
            f.write(b'CFGX') 
            f.write(struct.pack('B', 1)) 

            # 2. Serialize Root recursively
            self._write_node(f, self.root)

    def load_from_bin(self, file_path: str):
        """
        Loads state from a .cfgx binary file.
        """
        if not os.path.exists(file_path):
            raise ConfigPathNotFoundError(file_path)

        with open(file_path, 'rb') as f:
            # 1. Verify Magic
            magic = f.read(4)
            if magic != b'CFGX':
                raise ConfigInvalidFormatError("Invalid file signature. Expected 'CFGX'.")
            
            # 2. Verify Version
            version = struct.unpack('B', f.read(1))[0]
            if version != 1:
                raise ConfigInvalidFormatError(f"Unsupported file version: {version}")

            # 3. Deserialize Root
            self.root = self._read_node(f)

    def _write_node(self, f: io.BufferedWriter, node: Node):
        """
        Low-level binary packer.
        Format: [NameLen][Name][TypeTag][ValLen][Value][ChildCount][Children...]
        """
        # --- 1. NAME ---
        name_bytes = node.name.encode('utf-8')
        f.write(struct.pack('>I', len(name_bytes))) # 4 bytes, Big Endian
        f.write(name_bytes)

        # --- 2. VALUE & TYPE ---
        # Determine Tag and binary data
        tag = b'N' # Null/None
        val_bytes = b''

        if node.value is not None:
            if isinstance(node.value, bool):
                tag = b'B'
                val_bytes = struct.pack('?', node.value) # 1 byte bool
            elif isinstance(node.value, int):
                tag = b'I'
                # 8-byte long long for safety with large ints
                val_bytes = struct.pack('>q', node.value) 
            elif isinstance(node.value, float):
                tag = b'F'
                val_bytes = struct.pack('>d', node.value) # 8-byte double
            elif isinstance(node.value, str):
                tag = b'S'
                val_bytes = node.value.encode('utf-8')
            # Add more types here (List, Dict) as your system grows
        
        # Write Type Tag
        f.write(tag)
        
        # Write Value Length and Value
        f.write(struct.pack('>I', len(val_bytes)))
        f.write(val_bytes)

        # --- 3. CHILDREN ---
        children = list(node.children.values())
        f.write(struct.pack('>I', len(children))) # Child count
        
        for child in children:
            self._write_node(f, child) # Recursion

    def _read_node(self, f: io.BufferedReader) -> Node:
        """
        Low-level binary unpacker.
        """
        # --- 1. NAME ---
        # Read 4 bytes for name length
        raw_len = f.read(4)
        if not raw_len: return None # EOF check
        name_len = struct.unpack('>I', raw_len)[0]
        
        name = f.read(name_len).decode('utf-8')
        node = Node(name=name)

        # --- 2. VALUE & TYPE ---
        tag = f.read(1)
        val_len = struct.unpack('>I', f.read(4))[0]
        val_data = f.read(val_len)

        if tag == b'N':
            node.value = None
            node.type = None
        elif tag == b'B':
            node.value = struct.unpack('?', val_data)[0]
            node.type = "BOOL"
        elif tag == b'I':
            node.value = struct.unpack('>q', val_data)[0]
            node.type = "INT"
        elif tag == b'F':
            node.value = struct.unpack('>d', val_data)[0]
            node.type = "FLOAT"
        elif tag == b'S':
            node.value = val_data.decode('utf-8')
            node.type = "STR"
        
        # --- 3. CHILDREN ---
        child_count = struct.unpack('>I', f.read(4))[0]
        
        for _ in range(child_count):
            child = self._read_node(f)
            node.children[child.name] = child

        return node