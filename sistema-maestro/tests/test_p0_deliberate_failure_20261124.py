"""Temporary, intentional CI failure to test required contracts branch protection.
Never merge this file into main. Close the PR after recording the result.
"""
import unittest

class DeliberateFailure(unittest.TestCase):
    def test_required_contracts_check_blocks_merge(self):
        self.fail("P0 NEGATIVE TEST: expected CI failure on isolated PR; DO NOT MERGE")
