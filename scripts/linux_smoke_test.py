"""Minimal Linux-host smoke test for the broker-independent trading engine."""

import importlib

MODULES = (
    "pandas",
    "numpy",
    "requests",
    "dotenv",
)


def main() -> int:
    failed = []
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"OK: {module}")
        except Exception as exc:
            failed.append((module, str(exc)))
            print(f"FAIL: {module}: {exc}")

    if failed:
        return 1

    print("Linux trading-engine dependencies are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
