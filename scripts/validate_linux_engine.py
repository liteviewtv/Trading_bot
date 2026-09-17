"""Linux preflight for the cloud trading engine.

This intentionally validates only the broker-independent engine. It never
connects to an account or submits orders.
"""

import importlib
import sys

REQUIRED = ("pandas", "numpy", "requests", "dotenv")


def main() -> int:
    missing = []
    for name in REQUIRED:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    if missing:
        print("Missing Linux dependencies:", ", ".join(missing))
        return 1
    print("Linux trading engine preflight: OK")
    print("Broker execution: DISABLED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
