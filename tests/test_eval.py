import logging
import unittest
from xcomp.compiler_base import FileContextManager
from xcomp.compiler_base import CompilationError
from xcomp.eval import Evaluator
from xcomp.model import *

logging.getLogger('xcomp.eval').setLevel(logging.DEBUG)


class TestBase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.ctx_manager = FileContextManager()
        self.evaluator = Evaluator(self.ctx_manager)

    def eval(self, expr):
        result = self.evaluator.eval(expr)
        print(result)
        return result


class TestNamespaces(TestBase):
    def test_start_end(self):
        e = self.evaluator
        e.start_scope()
        self.assertEqual(e.scope_stack, [{}])
        self.assertEqual(e.namespace_stack, [None])
        e.end_scope()
        self.assertEqual(e.scope_stack, [])
        self.assertEqual(e.namespace_stack, [])

    def test_start_named(self):
        e = self.evaluator
        e.start_scope('foo')
        self.assertEqual(e.scope_stack, [{}])
        self.assertEqual(e.namespace_stack, ['foo'])
        e.end_scope()
        self.assertEqual(e.scope_stack, [])
        self.assertEqual(e.namespace_stack, [])

    def test_add_name(self):
        e = self.evaluator
        e.start_scope()
        e.add_name(NullPos, 'foo', 100)
        self.assertEqual(e.scope_stack, [{
            'foo': 100,
        }])
        self.assertEqual(e.namespace_stack, [None])

    def test_add_namespace(self):
        e = self.evaluator
        e.start_scope('bar')
        e.add_name(NullPos, 'foo', 100)
        self.assertEqual(e.scope_stack, [{
            'bar.foo': 100,
        }])
        self.assertEqual(e.namespace_stack, ['bar'])

    def test_add_namespace_nested(self):
        e = self.evaluator
        e.start_scope('foo')
        e.start_scope('bar')
        e.add_name(NullPos, 'baz', 100)
        self.assertEqual(e.scope_stack, [{
            # empty 'foo'
        },{
            'foo.bar.baz': 100,
        }])
        self.assertEqual(e.namespace_stack, ['foo', 'bar'])

    def test_merge(self):
        e = self.evaluator
        e.start_scope('foo')
        e.add_name(NullPos, 'gorf', 200)
        e.start_scope('bar')
        e.add_name(NullPos, 'baz', 100)
        self.assertEqual(e.scope_stack, [{
            'foo.gorf': 200,
        },{
            'foo.bar.baz': 100,
        }])
        e.end_scope(merge=True)
        self.assertEqual(e.scope_stack, [{
            'foo.gorf': 200,
            'foo.bar.baz': 100,
        }])

