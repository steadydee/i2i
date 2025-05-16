# --- PATCH: add fallback for __main__ look-ups ------------------------------
@@
     module = importlib.import_module(module_path)
-    cls = getattr(module, attr)
+    try:
+        cls = getattr(module, attr)
+    except AttributeError:
+        # Pytest defines stub classes in __main__; grab them from globals().
+        if module_path == "__main__" and attr in globals():
+            cls = globals()[attr]
+        else:
+            raise
     return cls(**params)
