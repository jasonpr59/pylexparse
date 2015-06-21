#!/usr/bin/env python
"""The pylexparse command-line driver."""

import sys

import graph_printer
import matcher
import regex


def main(args):
    """Parse arguments and dispatch the required subroutines."""
    subcommand = args[0]

    if subcommand == 'renfa':
        print _regex_to_nfa_dot(args[1])


def _regex_to_nfa_dot(regex_pattern):
    """Return a DOT graph representing a regular expression.

    Args:
       regex_pattern: A regular expression string.
    Returns: A multi-line string in DOT format.
    """
    pattern = regex.parse_regex(regex_pattern)
    nfa = matcher.pattern_to_nfa(pattern)
    return graph_printer.as_dot(nfa)


if __name__ == '__main__':
    main(sys.argv[1:])
