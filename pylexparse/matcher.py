"""Tools for matching input against patterns."""

import string

import nfa
import pattern



# NFA fragment producers will be registered into this dict.
fragment_producers = {}

# A decorator that registers a function to fragment_producers.  The
# decorator 'handles(some_type)' registers the decorated function
# as the one to apply to a pattern of type 'some_type'.
def handles(pattern_type):
    def decorator(handler):
        # Register the handler
        fragment_producers[pattern_type] = handler
        # Return the handler unchanged.
        return handler
    return decorator


@handles(str)
def string_to_fragment(pattern_str):
    if len(pattern_str) == 1:
        start, end = nfa.State(), nfa.State()
        start.add_transition(pattern_str, end)
        return nfa.Fragment(start, end)
    # Otherwise, we must chain together one fragment per character.
    return nfa.Fragment.chain(*(string_to_fragment(char) for char in pattern_str))


@handles(pattern.Sequence)
def sequence_to_fragment(sequence):
    return nfa.Fragment.chain(
        *(pattern_to_fragment(pattern) for pattern in sequence.patterns))


@handles(pattern.Star)
def star_to_fragment(star):
    pattern_frag = pattern_to_fragment(star.pattern)
    pattern_frag.end.add_empty_transition(pattern_frag.start)
    return nfa.Fragment(pattern_frag.start, pattern_frag.start)


@handles(pattern.Or)
def or_to_fragment(or_pat):
    # TODO(jasonpr): Update fragment intefrace so that the first
    # fragment doesn't seem special... since it isn't!
    first, rest = or_pat.patterns[0], or_pat.patterns[1:]

    result = pattern_to_fragment(first)
    result.add_in_parallel(*(pattern_to_fragment(pattern) for pattern in rest))

    return result


@handles(pattern.Maybe)
def maybe_to_fragment(maybe):
    fragment = pattern_to_fragment(maybe.pattern)
    fragment.start.add_empty_transition(fragment.end)
    return fragment


@handles(pattern.Anything)
def anything_to_fragment(pat):
    # TODO(jasonpr): Check that string.printable is what we want.
    return pattern_to_fragment(pattern.OneOf(string.printable))


@handles(pattern.OneOf)
def one_of_to_fragment(one_of):
    equivalent_pattern = pattern.Or(*(char for char in one_of.candidates))
    return pattern_to_fragment(equivalent_pattern)


@handles(pattern.Repeat)
def repeat_to_fragment(repeat):
    min_chain = nfa.Fragment.chain(
        *(pattern_to_fragment(repeat.pattern) for _ in range(repeat.times_min)))

    maybe_times = repeat.times_max - repeat.times_min
    if maybe_times:
        maybes = (pattern.Maybe(repeat.pattern) for _ in range(maybe_times))
        max_fragments = (pattern_to_fragment(pat) for pat in maybes)
        return nfa.Fragment.chain(min_chain, *max_fragments)
    else:
        return min_chain


@handles(pattern.Range)
def range_to_fragment(range_pat):
    low_index = ord(range_pat.low_character)
    high_index = ord(range_pat.high_character)
    chars = ''.join(chr(index) for index in range(low_index, high_index + 1))
    return pattern_to_fragment(pattern.OneOf(chars))


def pattern_to_fragment(pat):
    """Creates an NFA fragment matching a single pattern."""
    for pattern_type, fragment_producer in fragment_producers.iteritems():
        if isinstance(pat, pattern_type):
            return fragment_producer(pat)
    raise TypeError('Unexpected pattern type for: %s.' % pat)


def pattern_to_nfa(pat):
    return nfa.Nfa.from_fragment(pattern_to_fragment(pat))
