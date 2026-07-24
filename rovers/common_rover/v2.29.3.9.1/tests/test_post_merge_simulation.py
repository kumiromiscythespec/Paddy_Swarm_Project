import unittest
from case_runner import install_cases

class TestPostMerge(unittest.TestCase):
    pass

install_cases(TestPostMerge, 'post_merge')
