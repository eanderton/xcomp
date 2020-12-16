# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

"""Ansi-enhanced output printer library."""

import io
import sys
from colors import color
from colors import STYLES

default_style = {
    'display': 'inline',
    'padding-top': 0,
    'padding-bottom': 0,
    'before': '',
    'after': '',
    'bold': False,
    'italic': False,
    'underline': False,
    'color': None,
    'background': None,
    'faint': False,
    'blink': False,
    'blink2': False,
    'negative': False,
    'concealed': False,
    'crossed': False,
    'none': False,
}


class StylePrinterFn(object):
    """Function wrapper that also behaves like a context manager."""

    def __init__(self, ctx, style_name):
        """Creates a new instance around a printer context and a style name."""
        self.ctx = ctx
        self.style_name = style_name

    def __call__(self, *args, **kwargs):
        """Calls the wrapped printer and style with the provided args and kwargs."""
        return self.ctx.write(self.style_name, *args, **kwargs)

    def __enter__(self):
        """Returns a new printer based on the wrapped printer and style name.

        The new printer uses the same settings as the wrapped printer, but the default style
        is set to the style that corresponds to the wrapped style name."""

        p = StylePrinter(self.ctx.stream, self.ctx.stylesheet, self.ctx._get_style(self.style_name))
        p._start_newline = self.ctx._start_newline
        p.ansimode = self.ctx.ansimode
        return p

    def __exit__(self, type, value, traceback):
        """Placeholder for context management; does nothing."""
        pass


class StylePrinter(object):
    """Styled printer for generating ANSI decorated text."""

    def __init__(self, stream=None, stylesheet=None, style_defaults=None, ansimode=True):
        """Constructs an ansi-capable printer around a stream and stylesheet.

        The optional stream argument defaults to stdout if none is applied.

        The optional stylesheet argument is a dict of style names to
        a dict of style settings.  These settings are forwarded to the
        ansicolor `color` function as kwargs.  Please see the ansicolor
        module for more information.

        The optional style_defaults argument specifies the baseline for all
        styles in use by the printer.

        All public methods return self, such that chained calls are possible.

        This class provides a __getattr__ override that behaves like a proxy for
        write(style_name, ...).  This has a side-effect of allowing almost anything as
        a valid method name. As a result, invalid styles will still proxy to write()
        with no style applied.
        """

        self._start_newline = True
        self._style_defaults = style_defaults if style_defaults is not None else default_style
        self.ansimode = ansimode
        self.stream = stream if stream is not None else sys.stdout
        self.stylesheet = stylesheet if stylesheet is not None else {}

    def _get_style(self, style_name):
        """Gets the style for name, populated with defaults."""
        return dict(self._style_defaults, **self.stylesheet.get(style_name, {}))

    def write(self, style_name, text, *args, **kwargs):
        """Writes formatted text to the configured stream, in a specified style.

        If no args or kwargs are supplied, the `text` argument is applied literally. Otherwise,
        the *args and **kwargs arguments are applied against text using str.format.

        If the indicated style is not in the stylesheet, default style formatting is applied.
        """
        style = self._get_style(style_name)

        # handle display conditions for hidden, block, and start
        display = style['display']
        if display == 'hidden':
            return  # do nothing
        elif display in ['block', 'start'] and not self._start_newline:
            self.stream.write('\n')

        # emit the formatted text with padding and before/after style
        formatted_text = text.format(*args, **kwargs) if args or kwargs else text
        text = ('\n' * style['padding-top']) + style['before'] + formatted_text + \
            style['after'] + ('\n' * style['padding-bottom'])

        # emit to stream with or without ansi formatting
        if self.ansimode:
            self.stream.write(color(text, fg=style['color'], bg=style['background'],
                                    style='+'.join([k for k in STYLES if style[k]])))
        else:
            self.stream.write(text)

        # handle block condition and newline boolean
        if display in ['block', 'end']:
            self.stream.write('\n')
            self._start_newline = True
        else:
            self._start_newline = text.endswith('\n')
        return self

    def writeln(self, style_name, text, *args, **kwargs):
        """Identical to write(), except a newline is written afterwards."""
        self.write(style_name, text, *args, **kwargs)
        self.newline()
        return self

    def newline(self):
        """Writes a newline to the configured stream."""
        self.stream.write('\n')
        self._start_newline = True
        return self

    def nl(self):
        """Writes a newline to the configured stream."""
        return self.newline()

    def __getattr__(self, style_name):
        """Returns write wrapper for the style indicated by the attribute name."""
        return StylePrinterFn(self, style_name)


class StringPrinter(object):
    def __init__(self, stylesheet=None, style_defaults=None, ansimode=True):
        self.buf = io.StringIO()
        self.printer = StylePrinter(self.buf, stylesheet=stylesheet, style_defaults=style_defaults, ansimode=ansimode)

    def str(self):
        self.buf.seek(0)
        data = self.buf.read()
        self.buf.flush()
        self.buf.truncate()
        return data

    def __getattr__(self, name):
        return getattr(self.printer, name)


class StyleFormatter(object):
    def __init__(self, format_str=None, *args, **kwargs):
        self.printer = StringPrinter(*args, **kwargs)
        self.format_str = format_str or '{levelname}: {msg}'

    def format(self, record):
        kwargs = dict(record.__dict__)
        if record.args:
            kwargs.update(msg=record.msg % record.args)
        self.printer.writeln(record.levelname.lower(), self.format_str, **kwargs)
        return self.printer.str()


