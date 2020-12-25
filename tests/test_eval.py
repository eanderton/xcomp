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
        self.ctx_manager.files['<internal>'] = ''
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


class TestEval(TestBase):
    def test_cyclic_reference(self):
        e = self.evaluator
        e.start_scope()
        e.add_name(Pos(), 'foo', ExprName(Pos(), 'bar'))
        e.add_name(Pos(), 'bar', ExprName(Pos(), 'baz'))
        e.add_name(Pos(), 'baz', ExprName(Pos(), 'foo'))

        with self.assertRaisesRegex(CompilationError,
                r'<internal> \(1, 1\): cyclic reference when evaluating expression'):
            self.eval(ExprName(Pos(), 'foo'))

    def test_invert(self):
        e = self.evaluator
        pos = Pos()
        self.assertEqual(e.eval(ExprInvert(pos, ExprValue(pos, 0x03))), 0b11111100)

    def test_generate_fixup(self):
        e = self.evaluator
        e.start_scope()
        e.add_name(Pos(), 'foo', ExprValue(Pos(), 1000))
        e.start_scope()
        e.add_name(Pos(), 'foo', ExprValue(Pos(), 2000))
        e.start_scope()
        e.add_name(Pos(), 'foo', ExprValue(Pos(), 3000))

        foo = ExprName(Pos(), 'foo')
        fixup = e.get_fixup(foo)
        e.end_scope()
        e.end_scope()
        self.assertEqual(len(fixup.scope_stack), 3)
        self.assertEqual(e.eval(fixup), 3000)
        self.assertEqual(e.eval(foo), 1000)
