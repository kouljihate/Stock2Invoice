"""pytest configuration.

Most of what lives in ``tests/`` is not a pytest suite but a set of runnable
scripts (data generators, connection checks, browser walkthroughs). Several of
them talk to MongoDB or launch a browser at import time, so they are excluded
from collection here and stay runnable directly with ``python tests/<file>``.

Browser end-to-end tests are opt-in::

    RUN_E2E=1 python -m pytest tests/test_create_company.py

Add new unit tests as ``tests/test_*.py``; they are collected by default.
"""

import os

# Script runners: excluded from collection so a plain ``pytest`` stays fast
# and side-effect free. Run them explicitly with ``python tests/<file>``.
SCRIPT_RUNNERS = [
    'test_atlas_connection.py',
    'test_connection.py',
    'test_connection2.py',
    'test_connection3.py',
    'test_create_related.py',
    'test_import.py',
    'test_mongodb_connection.py',
    'test_p2p_procurement.py',
    'test_quote_lifecycle.py',
    'test_tls_settings.py',
    'simple_test.py',
    'final_po_test.py',
    'minimal_po_test.py',
    'simple_po_test.py',
]

# Playwright walkthroughs: need a server on BASE_URL and create real records.
E2E_MODULES = [
    'test_create_company.py',
    'test_po_procurement.py',
]

collect_ignore = list(SCRIPT_RUNNERS)

if os.getenv('RUN_E2E') != '1':
    collect_ignore += E2E_MODULES
