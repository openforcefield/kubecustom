"""
Unit and regression test for the kubecustom package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import kubecustom


def test_kubecustom_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "kubecustom" in sys.modules
