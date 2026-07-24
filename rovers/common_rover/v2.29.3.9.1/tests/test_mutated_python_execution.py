import unittest
from case_runner import install_cases

class TestPythonExecution(unittest.TestCase):
    pass

install_cases(TestPythonExecution, 'python_execution')
