from __future__ import annotations

import unittest

import untypy


@untypy.patch
class C:
    @untypy.patch
    def foo(self: C, d: D) -> C:
        return C()


@untypy.patch
class D:
    pass


class TestRecursion(unittest.TestCase):

    def test_recursion(self):
        # should not fail
        C().foo(D())
