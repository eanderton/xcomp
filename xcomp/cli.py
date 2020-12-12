# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

'''
Xcomp 6502 compiler suite.
'''

import os
import sys
import argparse
import io
import difflib
from .printer import StylePrinter
from .utils import *
from .settings import *
from .preprocessor import PreProcessor
from .compiler_base import FileContextManager
from .compiler import Compiler
from .decompiler import ModelPrinter


class Application(object):
    def __init__(self):
        # configure CLI parser
        parser = argparse.ArgumentParser(description=__doc__)
        subparsers = parser.add_subparsers(help='Sub-command help')
        parser.set_defaults(**cli_defaults)

        helper = subparsers.add_parser('help', help='Show help')
        helper.add_argument('topic', nargs='?', default=None,
                help='Topic to get help about')

        flags = argparse.ArgumentParser(add_help=False)
        flags.add_argument('--no-color', action='store_true',
                help='turns off ANSI colors')
        flags.add_argument('-d', '--debug', action='store_true',
                help='enable debug output')
        flags.add_argument('--trace', action='store_true',
                help='enable trace output')

        compiler_flags = argparse.ArgumentParser(add_help=False)
        compiler_flags.add_argument('-i', '--include', nargs='+', action='extend',
                help='Paths to search for included files')
        compiler_flags.add_argument('-s', '--segment', nargs='*', action='extend',
                choices=['zero', 'bss', 'data', 'text'],
                help='Segments to emit')
        compiler_flags.add_argument('source_file',
                help='Source file to process')

        compiler = subparsers.add_parser('compile', parents=[flags, compiler_flags],
                help='Compile program')
        compiler.add_argument('-o', '--output',
                help='Output file')
        compiler.add_argument('--out-format', choices=['raw', 'prg'],
                help='Output format')
        compiler.set_defaults(fn=self.do_compile, **cli_defaults)

        dump = subparsers.add_parser('dump', parents=[flags, compiler_flags],
                help='Dump compilation results to console')
        dump.set_defaults(fn=self.do_dump, **cli_defaults)

        preproc = subparsers.add_parser('preproc', parents=[flags, compiler_flags],
                help='Generate preprocessor output')
        preproc.set_defaults(fn=self.do_preprocess, **cli_defaults)

        fmt = subparsers.add_parser('fmt', parents=[flags],
                help='Re-formats a source file and displays a diff')
        fmt.add_argument('-t', '--test', action='store_true',
                help='Runs the formatter in test mode and does not rewrite file (lint)')
        fmt.add_argument('source_file',
                help='Source file to process')
        fmt.set_defaults(fn=self.do_fmt, **cli_defaults)

        parser.set_defaults(fn=self.do_help, topic=None, help_topics={
            'compile': compiler.format_help(),
            'dump': dump.format_help(),
            'preproc': preproc.format_help(),
            'help': helper.format_help(),
        })
        self.parser = parser

    def do_help(self):
        print(self.help_topics.get(self.topic, self.parser.format_help()))

    def do_dump(self):
        ctx_manager = FileContextManager(self.include)
        compiler = Compiler(ctx_manager)
        compiler.compile_file(self.source_file)
        start, end = compiler.extents()

        printer.title('Segment Data').nl()
        for name, seg in compiler.segments.items():
            seg = compiler.segments[name]
            printer.bold(f'  {name}: ')
            printer.text(f'${seg.start:04X}-${seg.end:04X}')
            printer.nl()
        printer.nl()

        printer.title('Hex Dump').nl()
        printer.text(f'Range: ${start:04X}-${end:04X}')
        printer.text(f' - Size: ${end-start:04X} ({end-start}) bytes').nl()
        print_hex(printer, compiler.data, start, end)

    def do_compile():
        ctx_manager = FileContextManager(self.include)
        compiler = Compiler(ctx_manager)
        compiler.compile_file(self.source_file)
        start, end = self.extents()
        header = None

        if out_format == 'raw':
            header = bytes([])
        elif out_format.lower() == 'prg':
            start_addr = compiler.pragma.get('c64_prg_start', 0x0801)
            header = intbytes(start_addr)

        with open(out, 'wb+') as f:
            f.write(header)
            f.write(compiler.data[start:end])

    def do_preprocess(ast):
        ctx_manager = FileContextManager(self.include)
        ast = PreProcessor(ctx_manager).parse(self.source_file)
        ModelPrinter(ansimode=not is_piped()).print_ast(ast)

    def do_fmt(self):
        ctx_manager = FileContextManager(self.include)
        text = ctx_manager.get_text(self.source_file)
        ast = PreProcessor(ctx_manager).parse(self.source_file)

        # print AST withoug ANSI formatting
        buf = io.StringIO()
        ModelPrinter(buf, ansimode=False).print_ast(ast)
        buf.seek(0)
        result = buf.read()

        # display the diff between the source and the formatted version
        diff = difflib.ndiff(text.split('\n'), result.split('\n'))
        if diff:
            for line in diff:
                style = diff_style[line[0]]
                printer.write(style, line).nl()
        if not test:
            # rewrite the original file
            real_filename = ctx_manager.search_file(self.source_file)
            with open(real_filename) as f:
                f.write(result)
        return bool(diff)

    def run(self, argv):
        """
        Entry point for CLI.

        Argument parsing, I/O configuration, and subcommmand dispatch are conducted here.
        """

        # parse args and set arguments directly to object attributes
        args = self.parser.parse_args(argv)
        self.__dict__.update(vars(args))
        self.printer = StylePrinter(stylesheet=default_stylesheet, ansimode=not is_piped())

        # debug output
        if args.debug:
            for k,v in vars(args).items():
                if k not in ['parser', 'printer', 'fn', 'help_topics']:
                    args.printer.key(k).value(str(v)).nl()

        # call handler
        try:
            args.fn()
        except Exception as e:
            if args.debug:
                raise
            args.printer.error(f'Error: {str(e)}').nl()
            return False
        return True


def main():
    app = Application()
    result = app.run(sys.argv[1:])
    sys.exit(0 if result is None or result else 1)
