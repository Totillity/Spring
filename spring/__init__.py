from .parser import parse
from .scanner import scan
from .spring_error import SpringError

__all__ = ['parse_text']


def parse_text(path: str, text: str):
    try:
        program = parse(scan(text))
    except SpringError as e:
        e.finish(path, text)
        raise Exception()
    return program
