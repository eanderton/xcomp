'''
Xcomp 6502 compiler suite.
'''

import os
import sys
import argparse
from pragma_utils.shims import to_bool
from pragma_utils.shims import is_piped
from pragma_utils.decorators import mapped_args
from .settings import printer

cli_defaults = {
    'no_color': to_bool(os.environ.get('XCOMP_NO_COLOR', 'false')),
    'debug': to_bool(os.environ.get('XCOMP_DEBUG', 'false')),
}


@mapped_args
def do_help(parser, help_topics, topic):
    print(help_topics.get(topic, parser.format_help()))


@mapped_args
def do_compile():
    printer.title('Compiling')
    printer.warn('Need to implement command').nl()


def main():
    """Entry point for CLI.

    Argument parsing, I/O configuration, and subcommmand dispatch are conducted here.
    """
    # configure CLI parser
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(help='Sub-command help')
    parser.set_defaults(cli_defaults)

    helper = subparsers.add_parser('help', help='Show help')
    helper.add_argument('topic', nargs='?', default=None, help='Topic to get help about')

    flags = argparse.ArgumentParser(add_help=False)
    flags.add_argument('--no-color', action='store_true', help='turns off ANSI colors')
    flags.add_argument('-d', '--debug', action='store_true', help='enable debug output')

    compiler = subparsers.add_parser('compile', parents=[flags], help='Compile program')
    compiler.add_argument('source_file', help='Source file to compile')
    compiler.set_defaults(fn=do_compile)

    parser.set_defaults(fn=do_help, topic=None, help_topics={
        'compile': compiler.format_help(),
        'help': helper.format_help(),
    })

    # parse args and clean up flags
    args = parser.parse_args()
    args.parser = parser

    # turn off ansi color on I/O redirect
    if is_piped():
        printer.ansimode = False

    return args.fn(**vars(args))

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
