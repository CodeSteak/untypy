import unittest

from test.util import DummyExecutionContext, DummyDefaultCreationContext
from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.list import ListFactory


class TestList(unittest.TestCase):

    def setUp(self) -> None:
        self.checker = ListFactory() \
            .create_from(list[int], DummyDefaultCreationContext())

        self.normal_list = [0, 1, 2, 3]
        self.wrapped_list = self.checker \
            .check_and_wrap(self.normal_list, DummyExecutionContext())

        self.faulty_normal_list = [0, 1, "2", 3]
        self.faulty_wrapped_list = self.checker \
            .check_and_wrap(self.faulty_normal_list, DummyExecutionContext())

    def test_side_effects(self):
        self.assertEqual(self.normal_list, self.wrapped_list)
        self.normal_list.append(4)
        self.assertEqual(self.normal_list, self.wrapped_list)
        self.wrapped_list.append(4)
        self.assertEqual(self.normal_list, self.wrapped_list)

    def test_error_delayed(self):
        checker = ListFactory() \
            .create_from(list[DummyDelayedType], DummyDefaultCreationContext())

        lst = checker \
            .check_and_wrap([1], DummyExecutionContext())

        res = lst[0]
        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[DummyDelayedType]")
        self.assertEqual(i, "     ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_wrapping_resp(self):
        """
        The wrapping call is responsable for ensuring the list
        wrapped is typed correctly
        """
        with self.assertRaises(UntypyTypeError) as cm:
            var = self.faulty_wrapped_list[2]

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_wrapping_resp_by_side_effects(self):
        """
        The wrapping call is responsable for side effects not causing
        type errors
        """
        self.normal_list.append("4")
        with self.assertRaises(UntypyTypeError) as cm:
            var = self.wrapped_list[4]

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_self_resp(self):
        """
        when appending the caller of append is responsable
        """
        with self.assertRaises(UntypyTypeError) as cm:
            self.wrapped_list.append("4")

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.last_responsable().file, __file__)

    def test_not_a_list(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.checker.check_and_wrap("Hello", DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_iterator(self):
        out = []
        for i in self.wrapped_list:
            out.append(i)

        self.assertEqual(out, [0, 1, 2, 3])

        with self.assertRaises(UntypyTypeError):
            for i in self.faulty_wrapped_list:
                out.append(i)

    def test_some_basic_ops(self):
        self.assertEqual(self.wrapped_list[1], 1)
        self.assertEqual(self.wrapped_list[:], [0, 1, 2, 3])
        self.assertEqual(self.wrapped_list[1:], [1, 2, 3])

        self.wrapped_list.append(4)
        self.assertEqual(self.wrapped_list, [0, 1, 2, 3, 4])

        self.wrapped_list.pop()
        self.assertEqual(self.wrapped_list, [0, 1, 2, 3])

        self.assertEqual(f"{self.wrapped_list}", f"{self.normal_list}")

        self.wrapped_list.append(4)
        self.assertEqual(self.wrapped_list + [5, 6], [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual([5,6] + self.wrapped_list, [5, 6, 0, 1, 2, 3, 4])
        self.assertEqual(self.wrapped_list + self.wrapped_list, [0,1,2,3,4,0,1,2,3,4])

        self.wrapped_list.extend([5, 6])
        self.assertEqual(self.wrapped_list, [0, 1, 2, 3, 4, 5, 6])

        self.wrapped_list.insert(0, 42)
        self.assertEqual(self.wrapped_list, [42, 0, 1, 2, 3, 4, 5, 6])

        self.wrapped_list.remove(4)
        self.assertEqual(self.wrapped_list, [42, 0, 1, 2, 3, 5, 6])
        self.wrapped_list.remove(42)
        self.wrapped_list.remove(5)
        self.wrapped_list.remove(6)
        self.wrapped_list.remove(0)
        self.assertEqual(self.wrapped_list, [1, 2, 3])

        x = self.wrapped_list.pop(1)
        self.assertEqual(x, 2)
        self.assertEqual(self.wrapped_list, [1, 3])

        self.assertRaises(UntypyTypeError, lambda: self.wrapped_list.append("foo"))
        l = self.wrapped_list.copy()
        self.assertEqual(l, self.wrapped_list)
        l.append("foo") # no more wrapper

    def test_equiv_with_builtin_list(self):
        self.check(lambda l: [42, 5] + l)
        self.check(lambda l: l + [42, 5])
        self.check(lambda l: 4 * l)
        self.check(lambda l: l * 3)
        def inPlaceAdd1(l):
            l += [5,6]
        self.check(inPlaceAdd1)
        def inPlaceAdd2(l):
            x = [5,6]
            x += l
            return x
        self.check(inPlaceAdd2)
        self.check(lambda l: 2 in l)
        self.check(lambda l: 42 in l)
        self.check(lambda l: l[0])
        self.check(lambda l: l[-2])
        self.check(lambda l: l[1:2])
        def sliceAssign1(l):
            l[0:2] = [5,6,7,8]
        self.check(sliceAssign1)
        def sliceAssign2(l):
            x = [0,1,2,3,4,5]
            x[1:4] = l
            return x
        self.check(sliceAssign2)
        def append(l):
            l.append(5)
        self.check(append)
        def extend1(l):
            l.extend([5,6])
        self.check(extend1)
        def extend2(l):
            x = [1,2,3,4,5,6,7]
            x.extend(l)
            return x
        self.check(extend2)
        self.check(lambda l: l.insert(1, 42))
        self.check(lambda l: l.remove(1))
        self.check(lambda l: l.pop())
        self.check(lambda l: l.pop(2))
        self.check(lambda l: l.clear())
        self.check(lambda l: l.index(4, 1, 3))
        self.check(lambda l: len(l))
        self.check(lambda l: l.count(1))
        self.check(lambda l: sorted(l))
        self.check(lambda l: l.sort())
        self.check(lambda l: l.sort(reverse=True))
        self.check(lambda l: l.sort(key=lambda i: -i))
        self.check(lambda l: list(reversed(l)))
        self.check(lambda l: l.reverse())
        self.check(lambda l: l.copy())
        self.check(lambda l: l == [1,4,2,1])
        self.check(lambda l:  [1,4,2,1] == l)
        self.check(lambda l: l != [1,4,2,1])
        self.check(lambda l:  [1,4,2,1] != l)
        self.check(lambda l: l < [1,4,2])
        self.check(lambda l:  [1,4,1] < l)
        self.check(lambda l: l <= [1,4,2])
        self.check(lambda l:  [1,4,1] <= l)
        self.check(lambda l: l > [1,4,2])
        self.check(lambda l:  [1,4,1] > l)
        self.check(lambda l: l >= [1,4,2])
        self.check(lambda l:  [1,4,1] >= l)


    def check(self, f):
        l = [1,4,2,1]
        refRes = f(l.copy())
        checker = ListFactory().create_from(list[int], DummyDefaultCreationContext())
        wrapped = checker.check_and_wrap(l, DummyExecutionContext())
        res = f(wrapped)
        self.assertEqual(l, wrapped)
        self.assertEqual(refRes, res)
