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
from xcomp.model import FileContextManager

module_path = os.path.dirname(os.path.abspath(__file__))

cli_defaults = {
    'no_color': to_bool(os.environ.get('XCOMP_NO_COLOR', 'false')),
    'debug': to_bool(os.environ.get('XCOMP_DEBUG', 'false')),
    'include': shlex.split(os.environ.get('XCOMP_INCLUDE', f'./ {module_path}/std')),
}

# TODO: pretty printing for exceptions
# TODO: pretty printer for token stream on preprocessor
# TODO: pretty printing on debug messages - use logging?

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

    import hexdump
    print(hexdump.dump(compiler.data))

@mapped_args
def do_preprocess(ctx_manager, debug, source_file):
    assert(ctx_manager)
    preproc = PreProcessor(ctx_manager)
    preproc.debug = debug
    ast = preproc.parse(source_file)

    for x in ast:
        printer.text(str(x)).newline()


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
