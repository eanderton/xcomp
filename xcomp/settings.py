# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import os
import shlex
from pragma_utils.shims import to_bool
from pragma_utils.shims import is_piped

module_path = os.path.dirname(os.path.abspath(__file__))

# default settings for styleprinter
default_stylesheet = {
    'text': {},
    'intro': {'display': 'block', 'color': 'green'},
    'title': {'display': 'block', 'color': 'white', 'bold': True, 'underline': True},
    'heading': {'display': 'start', 'padding-top': 1, 'color': 'white', 'bold': True},
    'subheading': {'display': 'start', 'before': '  ', 'after': ' ', 'color': 'yellow'},
    'on': {'color': 'green'},
    'off': {'color': 'red'},
    'error': {'color': 'red', 'bold': True},
    'debug': {'color': 'blue', 'italic': True},
    'info': {'color': 'green'},
    'warn': {'color': 'yellow'},
    'bold': {'bold': True},
    'underline': {'underline': True},

    # diff settings
    'removed': {'color': 'red'},
    'added': {'color': 'green'},
    'missing': {'color': 'blue'},
    'common': {},
}


cli_defaults = {
    'no_color': to_bool(os.environ.get('XCOMP_NO_COLOR', 'false')),
    'debug': to_bool(os.environ.get('XCOMP_DEBUG', 'false')),
    'trace': to_bool(os.environ.get('XCOMP_TRACE', 'false')),
    'include': shlex.split(os.environ.get('XCOMP_INCLUDE', f'./ {module_path}')),
    'segment': shlex.split(os.environ.get('XCOMP_SEGMENT_OUT', '')),
    'out': os.environ.get('XCOMP_OUT', './out.bin'),
    'out_format': os.environ.get('XCOMP_OUT_FORMAT', 'raw'),
}

diff_style = {
    '-': 'removed',
    '+': 'added',
    '?': 'missing',
    ' ': 'common',
}
