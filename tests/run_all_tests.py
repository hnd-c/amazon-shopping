"""Script to run all chemical database tests."""

import pytest
import sys
import os

def run_all_tests():
    """Run all test files."""
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # List of test files to run
    test_files = [
        'unit_tests/test_catalog_queries.py',
        'unit_tests/test_pricing_queries.py',
        'unit_tests/test_compliance_queries.py',
        'unit_tests/test_inventory_queries.py',
        'unit_tests/test_shipping_queries.py'
    ]

    # Convert paths to absolute paths
    test_paths = [os.path.join(current_dir, file) for file in test_files]

    # Run pytest with verbose output
    args = [
        '-v',  # verbose output
        '--tb=short',  # shorter traceback format
        '--show-capture=no',  # don't show captured stdout/stderr
        *test_paths
    ]

    return pytest.main(args)

if __name__ == '__main__':
    sys.exit(run_all_tests())