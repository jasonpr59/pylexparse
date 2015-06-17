class Pattern(object):
    """Base class for all patterns, besides strings"""

class Sequence(object):
    """The concatenation of two or more patterns."""

    def __init__(self, first, second, *rest):
        self.patterns = [first, second] + list(rest)

    def __repr__(self):
        return ''.join('(%s)' % pattern for pattern in self.patterns)


class Star(object):
    """Zero or more occurrences of a pattern."""

    def __init__(self, pattern):
        self.pattern = pattern

    def __repr__(self):
        return '(%s)*' % self.pattern


class Or(object):
    """Exactly one pattern from two or more candidates."""

    def __init__(self, first, second, *rest):
        self.patterns = [first, second] + list(rest)

    def __repr__(self):
        return '|'.join('(%s)' % pattern for pattern in self.patterns)


class Maybe(object):
    """Zero or one occurrences of a pattern."""

    def __init__(self, pattern):
        self.pattern = pattern

    def __repr__(self):
        return '(%s)?' % self.pattern


class Anything(object):
    """Matches any single character."""

    def __repr__(self):
        return '.'


class OneOf(object):
    """Matches any single character from a string of candidates."""

    def __init__(self, candidates):
        self.candidates = candidates

    def __repr__(self):
        return '[%s]' % self.candidates


class Repeat(object):
    """Matches a number of occurrences of a pattern, defined by a range."""

    def __init__(self, pattern, times_min, times_max=None):
        self.pattern = pattern
        self.times_min = times_min
        self.times_max = times_min if times_max is None else times_max

    def __repr__(self):
        return '(%s){%d,%d}' % (self.pattern, self.times_min, self.times_max)


class Range(object):
    """Matches any character in an inclusive range of ASCII characters."""

    def __init__(self, low_character, high_character):
        self.low_character = low_character
        self.high_character = high_character

    def __repr__(self):
        return '[%s-%s]' % (self.low_character, self.high_character)
