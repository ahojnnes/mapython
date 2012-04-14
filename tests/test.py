import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import test_map
import test_style


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_map.suite())
    suite.addTest(test_style.suite())
    return suite
