import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import test_map


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_map.suite())
    return suite
