'''
Xcomp 6502 compiler suite.
'''

import os
import sys
import argparse
import shlex
from pragma_utils.shims import to_bool
from pragma_utils.shims import is_piped
from pragma_utils.decorators import mapped_args
from .settings import printer
from xcomp.compiler import PreProcessor
from xcomp.compiler import Compiler
from xcomp.decompiler import ModelPrinter
from xcomp.model import FileContextManager

module_path = os.path.dirname(os.path.abspath(__file__))

cli_defaults = {
    'no_color': to_bool(os.environ.get('XCOMP_NO_COLOR', 'false')),
    'debug': to_bool(os.environ.get('XCOMP_DEBUG', 'false')),
    'include': shlex.split(os.environ.get('XCOMP_INCLUDE', f'./ {module_path}/std')),
}

# TODO: pretty printing for exceptions
# TODO: pretty printing on debug messages - use logging?

# TODO: I mean... just look at it.
def hexdump(src, start=0, end=None, length=16):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    end = (end or len(src))
    start -= start % length
    end -= end % length
    for c in range(start, end, length):
        chars = src[c:c+length]
        hex = ' '.join(["%02x" % x for x in chars])
        printable = ''.join(["%s" % ((x <= 127 and FILTER[x]) or '.') for x in chars])
        lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
    return ''.join(lines)

@mapped_args
def do_help(parser, help_topics, topic):
    print(help_topics.get(topic, parser.format_help()))


@mapped_args
def do_compile(ctx_manager, debug, source_file):
    preproc = PreProcessor(ctx_manager)
    preproc.debug = debug
    compiler = Compiler(ctx_manager)
    compiler.debug = debug
    compiler.compile(preproc.parse(source_file))

    with printer.underline as p:
        p.heading('Segment Data').nl()
    for name, seg in compiler.segments.items():
        seg = compiler.segments[name]
        printer.bold(f'{name}: ')
        printer.text(f'${seg.start:04X}-${seg.end:04X}')
        printer.newline()

    print(hexdump(compiler.data, 0x0800, 0x0900))


@mapped_args
def do_preprocess(ctx_manager, debug, source_file):
    preproc = PreProcessor(ctx_manager)
    preproc.debug = debug
    ast = preproc.parse(source_file)
    printer = ModelPrinter(ansimode=not is_piped())
    for x in ast:
        printer(x)


@mapped_args
def get_ctx_manager(include):
    return FileContextManager(include)


def main():
    """
    Entry point for CLI.

    Argument parsing, I/O configuration, and subcommmand dispatch are conducted here.
    """
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

    compiler_flags = argparse.ArgumentParser(add_help=False)
    compiler_flags.add_argument('-i', '--include', nargs='+', action='append',
            help='Paths to search for included files')
    compiler_flags.add_argument('source_file',
            help='Source file to process')

    compiler = subparsers.add_parser('compile', parents=[flags, compiler_flags],
            help='Compile program')
    compiler.set_defaults(fn=do_compile, **cli_defaults)

    pre = subparsers.add_parser('pre', parents=[flags, compiler_flags],
            help='Generate preprocessor output')
    pre.set_defaults(fn=do_preprocess, **cli_defaults)

    parser.set_defaults(fn=do_help, topic=None, help_topics={
        'compile': compiler.format_help(),
        'pre': pre.format_help(),
        'help': helper.format_help(),
    })

    # parse args and clean up flags
    args = parser.parse_args()
    args.parser = parser
    args = vars(args)

    if args['debug']:
        from pprint import pprint
        pprint(args)

    # turn off ansi color on I/O redirect
    if is_piped():
        printer.ansimode = False

    # get context manager and call handler
    args['ctx_manager'] = get_ctx_manager(**args)
    return args['fn'](**args)


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result is None or result else 1)
