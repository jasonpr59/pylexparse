import collections

import charsource
import matcher
import nfa
import regex

class Token(collections.namedtuple('Token', ['type_name', 'value'])):
    def __str__(self):
        return '%s(%r)' % (self.type_name, self.value)


class Rule(object):
    """The definition of a single token."""
    def __init__(self, name, regex, emitted=True):
        self.name = name
        self.regex = regex
        self.emitted = emitted


class Lexer(object):
    """A lexer for a list of token rules."""
    def __init__(self, rules):
        self._acceptor_rules = {}
        start, end = nfa.State(), nfa.State()
        for rule in rules:
            fragment = matcher.pattern_to_fragment(regex.parse_regex(rule.regex))
            acceptor = fragment.end
            self._acceptor_rules[acceptor] = rule
            start.add_empty_transition(fragment.start)
            fragment.end.add_empty_transition(end)

        # Add final EOF transition.
        # The regex for this rule is never used.
        # TODO(jasonpr): Allow a token to exist independently of its regex?
        eof_rule = Rule('EOF', '', emitted=False)
        eof_acceptor = nfa.State()
        # None is our EOF.
        start.add_transition(None, eof_acceptor)
        self._acceptor_rules[eof_acceptor] = eof_rule
        eof_acceptor.add_empty_transition(end)

        self._nfa = nfa.Nfa(start, self._acceptor_rules.keys())
        self._eof_rule = eof_rule

    def lex(self, input_str):
        """Break an input stream into tokens.

        Yields tokens from the input stream, for each token whose rule specifies
        emitted=True.
        """
        source = charsource.RewindSource(input_str)
        while True:
            acceptors, match = self._nfa.longest_match(source)

            # TODO(jasonpr): Resolve conflicting token types.
            assert len(acceptors) == 1
            acceptor = acceptors.pop()
            token = self._acceptor_rules[acceptor]

            if token is self._eof_rule:
                break

            assert len(match) > 0
            if token.emitted:
                yield Token(self._acceptor_rules[acceptor].name, match)
