"""Tools for parsing a regular expression into a Pattern."""

import collections
import string

import pattern as p

# Characters that represent themselves in a regular expression.
# TODO(jasonpr): Handle $ and ^ specially at edges of regex.
_CHAR_LITERALS = string.ascii_letters + string.digits + '!"#$%&\',-/:;<=>@^_`~] \t'
# Characters that represent themselves inside a square-bracket expression.
_GROUP_CHARS = string.ascii_letters + string.digits + '!"#$%&\'()*+,./:;<=>?@[^_`{|}~'
# Characters that represent themselves when escaped with a backslash.
_IDENTIY_ESCAPES = r'.[\()*+?{|'
# Characters that represent a character class when escaped with a backslash.
_CHARACTER_CLASSES = {
    'd': string.digits,
    'w': string.ascii_letters + string.digits + '_',
    'h': string.hexdigits,
    # TODO(jasonpr): Make an informed decision, rather than blindly
    # inheritting this definition from Python.
    's': string.whitespace,
    }

_BRACKET_CHARACTER_CLASSES = {
    'alnum': set(string.ascii_letters + string.digits),
    'alpha': set(string.ascii_letters),
    'digit': set(string.digits),
    'lower': set(string.ascii_lowercase),
    'print': set(string.printable),
    'punct': set(string.punctuation),
    # TODO(jasonpr): Make an informed decision, rather than blindly
    # inheritting this definition from Python.
    'space': set(string.whitespace),
    'upper': set(string.ascii_uppercase),
    'xdigit': set(string.hexdigits),
    }

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
        second_char = source.get()
        if second_char == '^':
            negating = True
        else:
            source.put(second_char)
            negating = False
        group_chars = _parse_group_chars(source)
        result = p.Selection(group_chars, negating)
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
    chars = set()

    while True:
        range_chars = _parse_group_range(source)
        if range_chars:
            for char in range_chars:
                chars.add(char)
            continue

        char_class = _parse_char_class(source)
        if char_class:
            chars |= char_class
            continue

        char = source.get()
        if not char:
            raise ValueError('Unexpected end of stream.')
        if char not in _GROUP_CHARS:
            source.put(char)
            break
        chars.add(char)

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
        escaped = source.get()
        if escaped in _IDENTIY_ESCAPES:
            return escaped
        elif escaped in _CHARACTER_CLASSES:
            return p.Selection(_CHARACTER_CLASSES[escaped])
        else:
            raise ValueError('Unexpected escape sequence, \\%s.', escaped)
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


def _parse_group_range(source):
    """Parse a three-character group range expression.

    Return the set of characters represented by the range.

    For example, parsing the expression 'c-e' from the source returns
    set(['c', 'd', 'e']).
    """
    start = source.get()
    if start not in _GROUP_CHARS:
        source.put(start)
        return None

    middle = source.get()
    if middle != '-':
        source.put(middle)
        source.put(start)
        return None

    end = source.get()
    if end not in _GROUP_CHARS:
        source.put(end)
        source.put(middle)
        source.put(start)
        return None

    range_chars = set()
    for ascii_value in range(ord(start), ord(end) + 1):
        range_chars.add(chr(ascii_value))
    return range_chars


def _parse_char_class(source):
    for class_name, class_contents in _BRACKET_CHARACTER_CLASSES.iteritems():
        if _parse_verbatim(source, '[:%s:]' % class_name):
            return class_contents
    return None


def _parse_verbatim(source, desired):
    """Consume a string, verbatim.

    Return whether the desired string was present.

    If the desired string wasn't present, push back all characters consumed
    during the execution of this function.
    """
    consumed = []
    for char in desired:
        consumed.append(source.get())
        if consumed[-1] != char:
            break
    else:
        # We consumed the whole thing!
        return True
    # We broke out when the consumed character diverged from the desired string.
    # Put everything pack before we return.
    for to_put_back in reversed(consumed):
        source.put(to_put_back)
    return False
