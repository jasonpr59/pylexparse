import string

import nfa

# TODO(jasonpr): Check that string.printable is what we want.
_ALL_CHARS = set(string.printable)

class Pattern(object):
    """Base class for all patterns, besides strings"""

    def compiled(self):
        return nfa.Nfa.from_fragment(self._fragment())

    def match(self, candidate):
        return bool(self.compiled().match(candidate))

def _string_to_fragment(pattern_str):
    if len(pattern_str) == 1:
        start, end = nfa.State(), nfa.State()
        start.add_transition(pattern_str, end)
        return nfa.Fragment(start, end)
    # Otherwise, we must chain together one fragment per character.
    return nfa.Fragment.chain(*(_string_to_fragment(char) for char in pattern_str))


class String(Pattern):
    def __init__(self, contents):
        self._contents = contents

    def __repr__(self):
        return self._contents

    def _fragment(self):
        return _string_to_fragment(self._contents)


class Sequence(Pattern):
    """The concatenation of one or more patterns."""

    def __init__(self, first, *rest):
        self.patterns = [first] + list(rest)

    def __repr__(self):
        return ''.join('(%s)' % pattern for pattern in self.patterns)

    def _fragment(self):
        return nfa.Fragment.chain(
            *(pattern._fragment() for pattern in self.patterns))

class Star(Pattern):
    """Zero or more occurrences of a pattern."""

    def __init__(self, pattern):
        self.pattern = pattern

    def __repr__(self):
        return '(%s)*' % self.pattern

    def _fragment(self):
        pattern_frag = self.pattern._fragment()
        pattern_frag.end.add_empty_transition(pattern_frag.start)
        return nfa.Fragment(pattern_frag.start, pattern_frag.start)

class Plus(Pattern):
    def __init__(self, pattern):
        self.pattern = pattern

    def __repr__(self):
        return '(%s)+' % self.pattern

    def _fragment(self):
        pattern_frag = plus.pattern._fragment()
        pattern_frag.end.add_empty_transition(pattern_frag.start)
        return pattern_frag

class Or(Pattern):
    """Exactly one pattern from one or more candidates."""

    def __init__(self, first, *rest):
        self.patterns = [first] + list(rest)

    def __repr__(self):
        return '|'.join('(%s)' % pattern for pattern in self.patterns)

    def _fragment(self):
        # TODO(jasonpr): Update fragment intefrace so that the first
        # fragment doesn't seem special... since it isn't!
        first, rest = self.patterns[0], self.patterns[1:]

        result = first._fragment()
        result.add_in_parallel(*(pattern._fragment() for pattern in rest))

        return result

class Maybe(Pattern):
    """Zero or one occurrences of a pattern."""

    def __init__(self, pattern):
        self.pattern = pattern

    def __repr__(self):
        return '(%s)?' % self.pattern

    def _fragment(self):
        fragment = self.pattern._fragment()
        fragment.start.add_empty_transition(fragment.end)
        return fragment



class Anything(Pattern):
    """Matches any single character."""

    def __repr__(self):
        return '.'

    def _fragment(self):
        return self.Selection(_ALL_CHARS._fragment())


class Selection(Pattern):
    """Matches any single character from a string of candidates."""

    def __init__(self, candidates, negating=False):
        self.candidates = candidates
        self.negating = negating

    def __repr__(self):
        return '[%s%s]' % ('^' if self.negating else '', self.candidates)

    def _fragment(self):
        start, end = nfa.State(), nfa.State()
        candidates = set(self.candidates)
        if self.negating:
            candidates = _ALL_CHARS - candidates
        for char in candidates:
            start.add_transition(char, end)
        return nfa.Fragment(start, end)


class Repeat(Pattern):
    """Matches a number of occurrences of a pattern, defined by a range."""

    def __init__(self, pattern, times_min, times_max=None):
        self.pattern = pattern
        self.times_min = times_min
        self.times_max = times_min if times_max is None else times_max

    def __repr__(self):
        return '(%s){%d,%d}' % (self.pattern, self.times_min, self.times_max)

    def _fragment(self):
        min_chain = nfa.Fragment.chain(
            *(self.pattern._fragment() for _ in range(self.times_min)))

        maybe_times = self.times_max - self.times_min
        if maybe_times:
            maybes = (pattern.Maybe(self.pattern) for _ in range(maybe_times))
            max_fragments = (pat._fragment() for pat in maybes)
            return nfa.Fragment.chain(min_chain, *max_fragments)
        else:
            return min_chain


class Range(Pattern):
    """Matches any character in an inclusive range of ASCII characters."""

    def __init__(self, low_character, high_character):
        self.low_character = low_character
        self.high_character = high_character

    def __repr__(self):
        return '[%s-%s]' % (self.low_character, self.high_character)

    def _fragment(self):
        low_index = ord(self.low_character)
        high_index = ord(self.high_character)
        chars = ''.join(chr(index) for index in range(low_index, high_index + 1))
        return pattern.Selection(chars._fragment())
