# ---------------------------------------------------------------------------
# Helper class
# ---------------------------------------------------------------------------
class AddableValuesDict(dict):
    """
    • Works like a dict
    •   x + y  merges dictionaries (right-side wins)
    • Allows attribute access  (state.prompt ≡ state["prompt"])
    """

    # merge operator
    def __add__(self, other):        # type: ignore[override]
        new = dict(self)
        new.update(other)
        return AddableValuesDict(new)

    # attribute getter
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    # attribute setter (so state.foo = 1 works)
    def __setattr__(self, name, value):
        self[name] = value
