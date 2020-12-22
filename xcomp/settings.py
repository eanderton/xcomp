# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import os
import shlex
from .utils import to_bool
from .utils import is_piped

# default settings for styleprinter
default_stylesheet = {
    'text': {},
    'intro': {'display': 'block', 'color': 'green'},
    'title': {'display': 'block', 'color': 'white', 'bold': True, 'underline': True},
    'heading': {'display': 'start', 'padding-top': 1, 'color': 'white', 'bold': True},
    'subheading': {'display': 'start', 'before': '  ', 'after': ' ', 'color': 'yellow'},

    # logging
    'error': {'color': 'red', 'bold': True},
    'debug': {'color': 'lightblue', 'italic': True},
    'info': {'color': 'green'},
    'warning': {'color': 'yellow'},
    'trace': {},

    # misc styles
    'bold': {'bold': True},
    'underline': {'underline': True},
    'on': {'color': 'green'},
    'off': {'color': 'red'},
    'key': {'color': 'white', 'bold': True, 'after': ': '},
    'value': {},

    # diff settings
    'removed': {'color': 'red'},
    'added': {'color': 'green'},
    'missing': {'color': 'blue'},
    'common': {},
}

# used for path-based cli defaults
module_path = os.path.dirname(os.path.abspath(__file__))

# command-line option settings with environment var alternatives
cli_defaults = {
    'no_color': to_bool(os.environ.get('XCOMP_NO_COLOR', 'false')),
    'debug': to_bool(os.environ.get('XCOMP_DEBUG', 'false')),
    'trace': shlex.split(os.environ.get('XCOMP_TRACE', '')),
    'include': shlex.split(os.environ.get('XCOMP_INCLUDE', f'./ {module_path}')),
    'segment': shlex.split(os.environ.get('XCOMP_SEGMENT_OUT', '')),
    'out': os.environ.get('XCOMP_OUT', './out.bin'),
    'out_format': os.environ.get('XCOMP_OUT_FORMAT', 'raw'),
    'mapfile': os.environ.get('XCOMP_MAPFILE', ''),
}

# style for diff output
diff_style = {
    '-': 'removed',
    '+': 'added',
    '?': 'missing',
    ' ': 'common',
}
