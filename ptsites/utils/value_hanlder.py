from dateutil.parser import parse


def handle_infinite(value):
    return '0' if value in ['.', '-', '--', '---', '∞', 'Inf', 'Inf.', '&inf', '无限', '無限'] else value


def handle_join_date(value):
    return parse(value).date()
