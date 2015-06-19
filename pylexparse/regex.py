"""Tools for parsing a regular expression into a Pattern."""

# TODO(jasonpr): Put add docstrings everywhere!

import collections
import string

import pattern as p


_CHAR_LITERALS = string.ascii_letters + string.digits + '!"#%&\',-/:;<=>@_`~'
_GROUP_CHARS = string.ascii_letters + string.digits + '!"#$%&\'()*+,./:;<=>?@[^_`{|}~'

class _CharSource(object):
    def __init__(self, iteratable):
        self._iterator = iter(iteratable)
        self._put_chars = collections.deque()

    def get(self):
        if self._put_chars:
            return self._put_chars.pop()
        try:
            return next(self._iterator)
        except StopIteration:
            # None is our EOF.
            return None

    def put(self, char):
        self._put_chars.append(char)


def parse_regex(regex_string):
    return _parse_regex(_CharSource(regex_string))


def _parse_regex(source):
    return _parse_alternation(source)


def _parse_alternation(source):
    parts = []
    # Act as though the last character was a '|', so we get the
    # initial element of the alternation.
    last_char = '|'
    while last_char == '|':
        parts.append(_parse_concatenation(source))
        last_char = source.get()
    # Put back the non-alternation character.
    source.put(last_char)

    return p.Or(*parts)


def _parse_concatenation(source):
    parts = []
    duplication = _parse_duplication(source)
    # If we're expecting a concatenation, there MUST be at least
    # one (first) element!
    assert duplication
    while duplication:
        parts.append(duplication)
        duplication = _parse_duplication(source)

    return p.Sequence(*parts)


def _parse_duplication(source):
    duplicated = _parse_parenthesization(source)
    if not duplicated:
        return None

    duplicator = source.get()

    if duplicator == '?':
        return p.Maybe(duplicated)
    elif duplicator == '*':
        return p.Star(duplicated)
    elif duplicator == '+':
        # TODO(jasonpr): Implement
        raise NotImplementedError('Regex "+" cannot yet be handled.')
    elif duplicator == '{':
        min_repeats = _parse_positive_int(source)
        range_continuation = source.get()

        # We will ultimately expect a closing curly brace, but
        # we might see a comma and a max repeats value, first.
        if range_continuation == ',':
            max_repeats = _parse_positive_int(source)
            range_continuation = source.get()
        else:
            max_repeats = min_repeats

        if range_continuation != '}':
            raise ValueError('Expected "}", but got "%s".' %
                             range_continuation)

        return p.Repeat(duplicated, min_repeats, max_repeats)
    else:
        source.put(duplicator)
        return duplicated


def _parse_parenthesization(source):
    first_char = source.get()
    if first_char == '(':
        enclosed_regex = _parse_regex(source)
        close_paren = source.get()
        assert close_paren == ')'
        return enclosed_regex

    # Otherwise, this must just be a group.  (Groups have just as
    # tight of binding as a parenthesization.)
    source.put(first_char)
    return _parse_group(source)


def _parse_group(source):
    first_char = source.get()
    if first_char == '[':
        group_chars = _parse_group_chars(source)
        result = p.OneOf(group_chars)
        close_brace = source.get()
        assert close_brace == ']'
        return result

    # Otherwise, it's a single normal character.
    source.put(first_char)
    return _parse_atom(source)

def _parse_group_chars(source):
    chars = []
    next_char = source.get()
    while next_char and next_char in _GROUP_CHARS:
        chars.append(next_char)
        next_char = source.get()
    source.put(next_char)
    return ''.join(chars)


def _parse_atom(source):
    char = source.get()

    if not char:
        # For good measure, put the EOF back on!
        # This doesn't really do anything, since the source will
        # generate EOFs forever.
        source.put(char)
        return None
    elif char == '.':
        return p.Anything()
    elif char in _CHAR_LITERALS:
        return char
    elif char == '\\':
        # TODO(jasonpr): Deal with escape sequences.
        raise NotImplementedError('Cannot yet handle escape sequences.')
    else:
        source.put(char)
        return None

def _parse_positive_int(source):
    digits = []
    next_char = source.get()
    assert next_char and next_char in string.digits
    while next_char and next_char in string.digits:
        digits.append(next_char)
        next_char = source.get()
    source.put(next_char)
    return int(''.join(digits))
