from configx.core.tree import ConfigTree

# 1. Setup Data
conf = ConfigTree()
conf.set("server.name", "Alpha")
conf.set("server.port", 8080)       # INT
conf.set("server.active", True)     # BOOL
conf.set("server.load", 45.5)       # FLOAT

print("Original Data:", conf.to_dict())

# 2. Save to Binary
conf.save_to_bin("system.cfgx")
print("Saved to system.cfgx")

# 3. Load from Binary (Simulate restart)
new_conf = ConfigTree()
new_conf.load_from_bin("system.cfgx")

print("Restored Data:", new_conf.to_dict())

# 4. Verify types preserved (Systems check)
port = new_conf._walk("server.port").value
print(f"Port is {port} (Type: {type(port)})") # Should be <class 'int'>, not string!