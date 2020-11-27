from pragma_utils.printer import StylePrinter

# default settings for styleprinter
default_stylesheet = {
    'text': {},
    'intro': {'display': 'block', 'color': 'green'},
    'title': {'display': 'block', 'color': 'white', 'bold': True, 'underline': True},
    'heading': {'display': 'start', 'padding-top': 1, 'color': 'white', 'bold': True},
    'subheading': {'display': 'start', 'before': '  ', 'after': ' ', 'color': 'yellow'},
    'on': {'color': 'green'},
    'off': {'color': 'red'},
    'error': {'color': 'red'},
    'debug': {'color': 'blue', 'italic': True},
    'info': {'color': 'green'},
    'warn': {'color': 'yellow'},
    'bold': {'bold': 'true'},
}

# singleton state for output printer
printer = StylePrinter(stylesheet=default_stylesheet)
