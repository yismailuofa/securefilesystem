import argparse
from typing import Optional


def tryParse(
    parser: argparse.ArgumentParser, line: str
) -> Optional[argparse.Namespace]:
    try:
        return parser.parse_args(line.split())
    except SystemExit:
        return None
