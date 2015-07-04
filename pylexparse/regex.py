"""Tools for parsing a regular expression into a Pattern."""

import collections
import string

import pattern as p

# Characters that represent themselves in a regular expression.
_CHAR_LITERALS = string.ascii_letters + string.digits + '!"#%&\',-/:;<=>@_`~'
# Characters that represent themselves inside a square-bracket expression.
_GROUP_CHARS = string.ascii_letters + string.digits + '!"#$%&\'()*+,./:;<=>?@[^_`{|}~'

class _CharSource(object):
    """An input source with getc() and ungetc() equivalents."""
    def __init__(self, iteratable):
        self._iterator = iter(iteratable)
        self._put_chars = collections.deque()

    def get(self):
        """Get the next character from the input stream."""
        if self._put_chars:
            return self._put_chars.pop()
        try:
            return next(self._iterator)
        except StopIteration:
            # None is our EOF.
            return None

    def put(self, char):
        """Put a character back onto the input stream.

        Characters are put back in LIFO order.
        """
        self._put_chars.append(char)


def parse_regex(regex_string):
    """Convert a regular expression string into a Pattern."""
    return _parse_regex(_CharSource(regex_string))


# The following _parse_* methods form a recursive descent parser
# that respect the order of operations in a regular expression.
def _parse_regex(source):
    """Parse any regex into a Pattern."""
    return _parse_alternation(source)


def _parse_alternation(source):
    """Parse an alternation expression, like 'ab|cd|ef'."""
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
    """Parse a concatenation expression, like 'abc' or 'a(b|c)d*'."""
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
    """Parse a duplication expression, like 'a*' or '(a|b){3,5}'."""
    duplicated = _parse_parenthesization(source)
    if not duplicated:
        return None

    duplicator = source.get()

    if duplicator == '?':
        return p.Maybe(duplicated)
    elif duplicator == '*':
        return p.Star(duplicated)
    elif duplicator == '+':
        return p.Plus(duplicated)
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
    """Parse a parenthesization pattern, like '(a|b)' or '[ab]' or 'a'.

    Note that '[ab]' is a parenthesization, since it is equivalent
    to '([ab])'.  Similarly, 'a' is equivalent to '(a)'.
    """
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
    """Parse a group pattern, like '[abc]' or 'a'.

    Note that 'a' is a group, since 'a' is equivalent to '[a]'.
    """
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
    """Parse the characters from a group specification.

    This is just a string of characters allowable in a group specification.
    For example, a valid parse is 'aA1.?', since '[aA1.?]' is a valid group.
    """
    chars = []
    next_char = source.get()
    while next_char and next_char in _GROUP_CHARS:
        chars.append(next_char)
        next_char = source.get()
    source.put(next_char)
    return ''.join(chars)


def _parse_atom(source):
    """Parse a single regex atom.

    An atom is a period ('.'), a character literal, or an escape sequence.
    """
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
    """Parse a positive integer.

    That is, parse a sequence of one or more digits.
    """
    digits = []
    next_char = source.get()
    assert next_char and next_char in string.digits
    while next_char and next_char in string.digits:
        digits.append(next_char)
        next_char = source.get()
    source.put(next_char)
    return int(''.join(digits))
