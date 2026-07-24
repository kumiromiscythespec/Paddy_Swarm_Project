import unittest
from case_runner import install_cases

class TestCrossRegistry(unittest.TestCase):
    pass

install_cases(TestCrossRegistry, 'cross_registry')
