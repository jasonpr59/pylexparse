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
        _regex_to_nfa_dot(args[1])

    if subcommand == 'match':
        _match_regex(args[1], args[2])

def _regex_to_nfa_dot(regex_pattern):
    """Print a DOT graph representing a regular expression."""
    pattern = regex.parse_regex(regex_pattern)
    nfa = matcher.pattern_to_nfa(pattern)
    print graph_printer.as_dot(nfa)


def _match_regex(regex_pattern, candidate):
    """Print whether a candidate string matches a regex pattern."""
    pattern = regex.parse_regex(regex_pattern)
    nfa = matcher.pattern_to_nfa(pattern)
    print nfa.match(candidate)


if __name__ == '__main__':
    main(sys.argv[1:])
