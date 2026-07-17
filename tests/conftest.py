# tests/conftest.py
"""
Shared pytest fixtures.

WHY a conftest.py?
──────────────────
Fixtures defined here are automatically available to all test modules
in this directory. This avoids duplicating setup/teardown logic across
test files, and pytest discovers conftest.py without any imports.
"""

import os
import sys

# Ensure the project root is on sys.path so `from backend.xxx` works
# even when running pytest from a subdirectory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
