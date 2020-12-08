# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import os
import stat
from inspect import signature


def to_bool(value):
    ''' Converts any value to a boolean. '''
    return str(value).lower() == "true"


def is_piped_stdin():
    ''' Returns true if stdin is on a pipe '''
    mode = os.fstat(sys.stdin.fileno()).st_mode
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode)


def is_piped():
    ''' Returns true if the program has either stdin or stdout on a pipe.'''
    return os.fstat(0) != os.fstat(1)


def lobyte(value):
    return value & 0xFF


def hibyte(value):
    return (value >> 8) & 0xFF


def is8bit(value):
    return lobyte(value) == value


def stringbytes(value, encoding):
    return list([x for x in bytes(value, encoding)])


def intbytes(value):
    return bytes([lobyte(value), hibyte(value)])


def mapped_args(fn):
    '''
    Function wrapper that only passes kwargs that map to the wrapped function.
    '''

    def impl(**kwargs):
        fn_kwargs={}
        for k in signature(fn).parameters:
            fn_kwargs[k] = kwargs[k]
        return fn(**fn_kwargs)

    return impl


def fixture(name, handler):
    def wrapper(fn):
        def impl(*args, **kwargs):
            kwargs[name] = handler(*args, **kwargs)
            return fn(*args, **kwargs)
        return impl
    return wrapper


# TODO: pretty printing on debug messages - use logging?
# TODO: encoding support for the data
def print_hex(printer, data, start=0, end=0xFFFF, stride=16):
    for line_start in range(start, end, stride):
        line_end = min(line_start + stride, end)
        line = data[line_start:line_end]

        byte_str = ' '.join([f'{x:02X}' for x in line])
        byte_str += ' '  * ((stride * 3) - len(byte_str))

        #encoding = 'petscii-c64en-uc'
        #print(type(line), len(line))
        #print('firstchar', bytes(line[0]))
        #linechars = []
        #for ii in range(len(line)):
        #    ch = line[ii]
        #    print('ch', ii, ch, bytes([ch]))
        #    try:
        #        linechars.append(bytes([ch]).decode('utf-8')) #.encode('utf-8'))
        #    except:
        #        linechars.append('.')
        #print('linechars', linechars) #.encode('utf-8'))

        utf_filter = lambda ch: chr(ch) if ch > 32 else '.'
        #text = ''.join(map(utf_filter, line))
        text = ''
        printer.text(f'{line_start:04X}  {byte_str} {text}').nl()


