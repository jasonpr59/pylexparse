import collections

class State(object):
    def __init__(self):
        self._transitions = collections.defaultdict(set)

    def add_transition(self, character, destination):
        assert character not in self._transitions, (
            'Cannot re-add transition for character %s' % character)
        self._transitions[character] = destination

    def __iter__(self):
        return self._transitions.iteritems()

    def successors(self):
        return self._transitions.values()


class Dfa(object):
    def __init__(self, start, accepting_states):
        self.start = start
        self.accepting_states = set(accepting_states)

