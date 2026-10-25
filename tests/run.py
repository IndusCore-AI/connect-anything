#!/usr/bin/env python3
"""Run the tests with one command.

  python3 tests/run.py            offline: no network, no model calls (about a minute)
  python3 tests/run.py --online   also the acceptance tests, which fetch the real sources from GitHub
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "scripts"), HERE]

online = "--online" in sys.argv
argv = [a for a in sys.argv[1:] if a != "--online"]
scratch = tempfile.mkdtemp(prefix="ca-tests-")
os.environ["CA_TEST_TMP"] = scratch
if not online:
    os.environ["CONNECT_ANYTHING_HOME"] = os.path.join(scratch, "home")  # staging stays out of ~/.connect-anything

loader = unittest.TestLoader()
suite = loader.loadTestsFromName("test_engine")
if online:
    suite.addTests(loader.loadTestsFromName("test_online"))
result = unittest.TextTestRunner(verbosity=2 if "-v" in argv else 1).run(suite)
print(f"\nscratch: {scratch}")
sys.exit(0 if result.wasSuccessful() else 1)
