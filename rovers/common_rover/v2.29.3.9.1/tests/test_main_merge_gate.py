import unittest
from case_runner import install_cases

class TestMainGate(unittest.TestCase):
    pass

install_cases(TestMainGate, 'main_gate')
