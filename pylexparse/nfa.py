"""NFA datatypes, and tools to build them."""

import collections

import charsource
from fixed_point import fixed_point

class State(object):
    """A state of a Nondeterministic Finite Automaton.

    Includes outgoing transitions, instances reference other states.
    """

    def __init__(self):
        self._transitions = collections.defaultdict(set)

    def add_transition(self, character, destination):
        """Specify a transition to a new state via a character."""
        self._transitions[character].add(destination)

    def add_empty_transition(self, destination):
        """Add an empty transition to another state."""
        self.add_transition('', destination)

    def __iter__(self):
        """Get an iterator over outgoing transitions.

        Yields: A (character, destination_state) pair for each outgoing
           transition.
        """
        for character, destinations in self._transitions.iteritems():
            for destination in destinations:
                yield (character, destination)

    def successors(self):
        """Yield all successor states of this state.

        If some successor is reached via multiple edges, it will be
        yielded as many times.
        """
        for unused_character, destination in self:
            yield destination

    def follow(self, character):
        return self._transitions[character]


class Fragment(object):
    """A piece of an NFA graph with a single start and single end.

    Used for assembling an NFA from smaller NFAs.
    """

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def append(self, follower):
        """Connect an NFA fragement to the end of this one.

        That is, adds a transition from this Fragment's end state to the
        other Fragment's begin state, and updates this Fragment to
        represent the entire new graph.

        Once an Fragment is connected to another one, it becomes unusable.
        At this point, no code should operate on this dead Fragment,
        neither by attempting to make other connections nor by accessing
        States inside it.
        """
        self.end.add_empty_transition(follower.start)
        self.end = follower.end
        # TODO(jasonpr): Consider somehow ruining follower, so nobody
        # attempts to use the old, unusable fragment.

    def add_in_parallel(self, *siblings):
        """Connect an NFA fragment in parallel with this one.

        See 'append' for a warning against using any sibling once it has
        been connected to another fragment.
        """
        new_start, new_end = State(), State()

        parts = [self] + list(siblings)

        for part in parts:
            new_start.add_empty_transition(part.start)
            part.end.add_empty_transition(new_end)

        self.start, self.end = new_start, new_end

        # TODO(jasonpr): Consider somehow ruining the siblings, so nobody
        # attempts to use the old, unusable fragment.

    @staticmethod
    def chain(first, *rest):
        chain = first
        for fragment in rest:
            chain.append(fragment)
        return chain


class Nfa(object):
    """A Nondeterministic Finite Automaton.

    Most of the structure of this automaton is not actually contained in
    instances of Nfa.  Instead, the structure is given by the States
    reachable from the start state.
    """

    def __init__(self, start, accepting_states):
        self.start = start
        self.accepting = set(accepting_states)

    @classmethod
    def from_fragment(cls, fragment):
        return cls(fragment.start, [fragment.end])

    def match(self, candidate):
        """Match the candidate against this NFA.

        Return matching states.
        """
        states, match = self.longest_match(charsource.RewindSource(candidate))
        return states if match == candidate else set()


    def longest_match(self, source):
        """Find the longest match, starting from the first character.

        Args:
            source: A RewindSource of characters.
        Return (matching states, matching string) tuple.
        """
        states = set(epsilon_closure(self.start))

        match = set(), 0

        for i, char in enumerate(source):
            if not states:
                break
            acceptors = states & self.accepting
            if acceptors:
                match = acceptors, i
            states = advance(states, char)
        length = i + 1

        # Do one more check after the final advance step.
        acceptors = states & self.accepting
        if acceptors:
            match = acceptors, length

        matching_states, match_length = match
        matching_string = source.disown_first(match_length)
        source.rewind()
        return matching_states, matching_string


def advance(states, char):
    """Find all states to which any input state could advance,
       along the given character."""
    next_states = set()
    for state in states:
        next_states |= state.follow(char)
    return multi_epsilon_closure(next_states)


@fixed_point(set)
def epsilon_closure(state, _epsilon_closure):
    """Find all states that can be reached by following empty transitions.

    In contrast with the usual description of the epsilon closure,
    this function takes a single state as its input.  Our
    multi_epsilon_closure takes a set of states, and returns the union
    of their epsilon clousres.
    """
    result = set([state])
    for follower in state.follow(''):
        result |= _epsilon_closure(follower)
    return result

def multi_epsilon_closure(states):
    """Find the epsilon closure of several states and return their union."""
    result = set()
    for state in states:
        result |= epsilon_closure(state)
    return result
